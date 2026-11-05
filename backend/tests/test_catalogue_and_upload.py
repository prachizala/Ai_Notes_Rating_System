import io
import fitz
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models import Stream, Semester, User
from app.core.security import hash_password, create_access_token


def make_valid_pdf_bytes(text: str = "NoteIQ test content for academic evaluation") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
async def seeded_test_db():
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

    # Seed streams, semesters, and test users
    async with session_maker() as session:
        bca = Stream(name="Bachelor of Computer Applications", slug="bca")
        bba = Stream(name="Bachelor of Business Administration", slug="bba")
        session.add_all([bca, bba])

        for n in range(1, 6):
            session.add(Semester(number=n, status="active"))
        session.add(Semester(number=6, status="coming_soon"))

        user1 = User(
            name="Alice Faculty",
            email="alice@college.edu",
            password_hash=hash_password("Password123!"),
            role="faculty",
        )
        user2 = User(
            name="Bob Student",
            email="bob@college.edu",
            password_hash=hash_password("Password123!"),
            role="student",
        )
        session.add_all([user1, user2])
        await session.commit()
        await session.refresh(user1)
        await session.refresh(user2)

        user1_id = str(user1.id)
        user2_id = str(user2.id)

    yield {"user1_id": user1_id, "user2_id": user2_id}

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_catalogue_endpoints(seeded_test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Get streams
        res = await client.get("/api/v1/streams")
        assert res.status_code == 200
        streams = res.json()
        assert len(streams) == 2
        bca = next(s for s in streams if s["slug"] == "bca")

        # 2. Get semesters for BCA
        res_sem = await client.get(f"/api/v1/streams/{bca['id']}/semesters")
        assert res_sem.status_code == 200
        sems = res_sem.json()
        assert len(sems) == 6
        sem6 = next(s for s in sems if s["number"] == 6)
        assert sem6["status"] == "coming_soon"

        # 3. Get subjects initially empty (since no documents exist yet)
        res_sub = await client.get("/api/v1/subjects?stream=bca&semester=1")
        assert res_sub.status_code == 200
        assert res_sub.json() == []


@pytest.mark.anyio
async def test_semester_6_rejection(seeded_test_db):
    user_id = seeded_test_db["user1_id"]
    token = create_access_token(subject=user_id, role="faculty")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"access_token": token}) as client:
        pdf_bytes = make_valid_pdf_bytes()
        res = await client.post(
            "/api/v1/documents",
            data={
                "stream": "bca",
                "semester": 6,  # Semester 6 is Coming Soon
                "subject": "Cloud Computing",
                "topic": "Microservices",
                "title": "Cloud Lecture 1",
            },
            files={"file": ("lecture.pdf", pdf_bytes, "application/pdf")},
        )
        assert res.status_code == 400
        assert "Semester 6 is Coming Soon" in res.json()["message"]


@pytest.mark.anyio
async def test_upload_normalization_and_duplicate_prevention(seeded_test_db):
    user_id = seeded_test_db["user1_id"]
    token = create_access_token(subject=user_id, role="faculty")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", cookies={"access_token": token}) as client:
        pdf_bytes = make_valid_pdf_bytes("Unique C Programming Notes")

        # 1. First upload: 'C Programming!!' and 'Pointers & Memory'
        res1 = await client.post(
            "/api/v1/documents",
            data={
                "stream": "bca",
                "semester": 1,
                "subject": "C Programming!!",
                "topic": "Pointers & Memory",
                "title": "Complete C Pointers Guide",
                "description": "Comprehensive guide to pointers.",
            },
            files={"file": ("pointers.pdf", pdf_bytes, "application/pdf")},
        )
        assert res1.status_code == 201
        doc1 = res1.json()
        assert doc1["status"] == "queued"
        assert doc1["uploader_name"] == "Alice Faculty"
        assert doc1["uploader_role"] == "faculty"

        # 2. Check catalogue now shows this subject
        res_sub = await client.get("/api/v1/subjects?stream=bca&semester=1")
        assert res_sub.status_code == 200
        subjects = res_sub.json()
        assert len(subjects) == 1
        assert subjects[0]["name"] == "C Programming!!"
        assert subjects[0]["normalized_name"] == "c programming"
        assert subjects[0]["document_count"] == 1

        # 3. Duplicate upload with same file under normalized subject 'c   programming' and topic 'pointers   memory'
        res_dup = await client.post(
            "/api/v1/documents",
            data={
                "stream": "bca",
                "semester": 1,
                "subject": "c   programming",
                "topic": "pointers   memory",
                "title": "Duplicate Pointers",
            },
            files={"file": ("pointers_copy.pdf", pdf_bytes, "application/pdf")},
        )
        assert res_dup.status_code == 409
        assert "identical document has already been uploaded" in res_dup.json()["message"]


@pytest.mark.anyio
async def test_owner_only_patch_and_delete_and_download(seeded_test_db):
    user1_id = seeded_test_db["user1_id"]
    user2_id = seeded_test_db["user2_id"]
    token_owner = create_access_token(subject=user1_id, role="faculty")
    token_other = create_access_token(subject=user2_id, role="student")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Owner uploads a document
        client.cookies.set("access_token", token_owner)
        pdf_bytes = make_valid_pdf_bytes("Data Structures Binary Trees")
        res_upload = await client.post(
            "/api/v1/documents",
            data={
                "stream": "bca",
                "semester": 2,
                "subject": "Data Structures",
                "topic": "Binary Trees",
                "title": "Trees Overview",
            },
            files={"file": ("trees.pdf", pdf_bytes, "application/pdf")},
        )
        assert res_upload.status_code == 201
        doc_id = res_upload.json()["id"]

        # Other user tries to PATCH title -> 403 Forbidden
        client.cookies.set("access_token", token_other)
        res_patch_forbidden = await client.patch(
            f"/api/v1/documents/{doc_id}",
            json={"title": "Hacked Title"},
        )
        assert res_patch_forbidden.status_code == 403

        # Other user tries to DELETE -> 403 Forbidden
        res_del_forbidden = await client.delete(f"/api/v1/documents/{doc_id}")
        assert res_del_forbidden.status_code == 403

        # Authenticated user downloads -> increments count and returns signed URL
        res_dl = await client.get(f"/api/v1/documents/{doc_id}/download")
        assert res_dl.status_code == 200
        assert "download_url" in res_dl.json()
        assert res_dl.json()["filename"] == "trees.pdf"

        # Owner patches title -> 200 OK
        client.cookies.set("access_token", token_owner)
        res_patch_ok = await client.patch(
            f"/api/v1/documents/{doc_id}",
            json={"title": "Updated Trees Guide"},
        )
        assert res_patch_ok.status_code == 200
        assert res_patch_ok.json()["title"] == "Updated Trees Guide"

        # Owner deletes document -> 200 OK
        res_del_ok = await client.delete(f"/api/v1/documents/{doc_id}")
        assert res_del_ok.status_code == 200

        # Check document is gone
        res_get = await client.get(f"/api/v1/documents/{doc_id}")
        assert res_get.status_code == 404
