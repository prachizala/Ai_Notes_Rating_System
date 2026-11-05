import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.rate_limit import _memory_limits


@pytest.fixture
async def async_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_register_and_login_flow(async_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new user
        reg_payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "Password123!",
            "role": "student",
        }
        res = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == "jane@example.com"
        assert data["user"]["role"] == "student"
        assert "access_token" in res.cookies
        assert "refresh_token" in res.cookies
        assert "csrf_token" in res.cookies

        # 2. Duplicate email should fail with 400
        res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_dup.status_code == 400
        assert "already exists" in res_dup.json()["message"]

        # 3. Login with wrong password should fail with 401
        res_wrong = await client.post(
            "/api/v1/auth/login",
            json={"email": "jane@example.com", "password": "WrongPassword!"},
        )
        assert res_wrong.status_code == 401

        # 4. Login with correct password
        res_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "jane@example.com", "password": "Password123!"},
        )
        assert res_login.status_code == 200
        assert "access_token" in res_login.cookies

        # 5. Get current user profile (/me)
        res_me = await client.get("/api/v1/auth/me")
        assert res_me.status_code == 200
        assert res_me.json()["email"] == "jane@example.com"

        # 6. Logout
        res_logout = await client.post("/api/v1/auth/logout")
        assert res_logout.status_code == 200


@pytest.mark.anyio
async def test_protected_route_without_token(async_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/auth/me")
        assert res.status_code == 401


@pytest.mark.anyio
async def test_password_length_validation(async_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Short Pass",
                "email": "short@example.com",
                "password": "123",  # Under 8 characters
                "role": "student",
            },
        )
        assert res.status_code == 422


@pytest.mark.anyio
async def test_rate_limiting_auth(async_db):
    transport = ASGITransport(app=app)
    _memory_limits.clear()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger login with incorrect password until 429
        for i in range(15):
            res = await client.post(
                "/api/v1/auth/login",
                json={"email": f"test{i}@example.com", "password": "wrong"},
            )
            assert res.status_code == 401

        # 16th attempt should hit rate limit (429)
        res_limit = await client.post(
            "/api/v1/auth/login",
            json={"email": "test16@example.com", "password": "wrong"},
        )
        assert res_limit.status_code == 429
