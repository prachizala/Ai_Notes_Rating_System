import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models import (
    Document,
    DocumentAnalysis,
    DocumentChunk,
    Semester,
    Stream,
    Subject,
    Topic,
    User,
)
from app.core.security import hash_password, create_access_token


@pytest.fixture
async def chat_test_db():
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

    async with session_maker() as session:
        user = User(
            name="Alice",
            email="alice@test.edu",
            password_hash=hash_password("password123"),
            role="student",
        )
        session.add(user)
        await session.commit()
        user_id = str(user.id)

    yield {"user_id": user_id, "session_maker": session_maker}

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_empty_database_yields_zero_and_no_hallucinations(chat_test_db):
    user_id = chat_test_db["user_id"]
    token = create_access_token(subject=user_id, role="student")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", token)

        # 1. "How many notes are available" on empty DB
        res1 = await client.post("/api/v1/chat", json={"message": "How many notes are available?"})
        assert res1.status_code == 200
        data1 = res1.json()
        assert "0 verified academic notes" in data1["message"]["content"]
        assert data1["message"]["sources"] == []

        # 2. "Show all BCA Semester 1 notes" on empty DB
        res2 = await client.post("/api/v1/chat", json={"message": "Show all BCA Semester 1 notes"})
        assert res2.status_code == 200
        assert "No notes are currently uploaded" in res2.json()["message"]["content"]

        # 3. "Which subjects have notes" on empty DB
        res3 = await client.post("/api/v1/chat", json={"message": "Which subjects have notes?"})
        assert res3.status_code == 200
        assert "No subjects currently have notes" in res3.json()["message"]["content"]


@pytest.mark.anyio
async def test_populated_database_queries(chat_test_db):
    session_maker = chat_test_db["session_maker"]
    user_id = chat_test_db["user_id"]
    token = create_access_token(subject=user_id, role="student")

    # Populate sample course notes
    async with session_maker() as session:
        bca = Stream(name="BCA", slug="bca")
        sem1 = Semester(number=1, status="active")
        session.add_all([bca, sem1])
        await session.commit()

        u = await session.get(User, uuid.UUID(user_id))

        c_prog = Subject(stream_id=bca.id, semester_id=sem1.id, name="C Programming", normalized_name="c programming")
        session.add(c_prog)
        await session.commit()

        arrays_topic = Topic(subject_id=c_prog.id, name="Arrays", normalized_name="arrays")
        session.add(arrays_topic)
        await session.commit()

        doc1 = Document(
            subject_id=c_prog.id,
            topic_id=arrays_topic.id,
            uploader_id=u.id,
            title="Introduction to C Arrays",
            file_key="key/arrays.pdf",
            original_filename="arrays.pdf",
            file_type="pdf",
            file_size=1024,
            checksum_sha256="checksum1234",
            status="complete",
        )
        session.add(doc1)
        await session.commit()

        analysis = DocumentAnalysis(
            document_id=doc1.id,
            version=1,
            rubric_version="v1",
            model_name="fake-model",
            accuracy_score=4.5,
            explanation_score=4.5,
            depth_score=4.0,
            examples_score=4.0,
            overall_score_raw=4.3,
            overall_score_display=4.5,
            summary="Great notes on array indexing and traversal.",
            total_topics=1,
        )
        session.add(analysis)

        chunk1 = DocumentChunk(
            document_id=doc1.id,
            chunk_index=0,
            location="Page 1",
            text="In C, an array is a collection of elements of identical data type placed in contiguous memory locations.",
            embedding=[0.05] * 768,
        )
        session.add(chunk1)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", token)

        # 1. Count notes
        r1 = await client.post("/api/v1/chat", json={"message": "how many notes are available?"})
        assert "1 verified academic notes" in r1.json()["message"]["content"]

        # 2. Show all BCA Semester 1 notes
        r2 = await client.post("/api/v1/chat", json={"message": "show all bca semester 1 notes"})
        assert "Introduction to C Arrays" in r2.json()["message"]["content"]

        # 3. Which subjects have notes
        r3 = await client.post("/api/v1/chat", json={"message": "which subjects have notes"})
        assert "C Programming" in r3.json()["message"]["content"]

        # 4. Are Array notes available
        r4 = await client.post("/api/v1/chat", json={"message": "are array notes available"})
        assert "Yes, notes covering 'array' are available" in r4.json()["message"]["content"]

        # 5. Highest rated notes / Best notes for C Programming
        r5 = await client.post("/api/v1/chat", json={"message": "best notes for C Programming"})
        assert "Introduction to C Arrays" in r5.json()["message"]["content"]

        # 6. Topics without notes (should state no syllabus checklist exists)
        r6 = await client.post("/api/v1/chat", json={"message": "topics with no notes for C Programming"})
        assert "No reference syllabus checklist exists" in r6.json()["message"]["content"]

        # 7. Explain a concept using uploaded notes (RAG hybrid search)
        r7 = await client.post("/api/v1/chat", json={"message": "Explain how arrays are laid out in memory"})
        assert r7.status_code == 200
        data7 = r7.json()
        assert len(data7["message"]["sources"]) >= 1
        assert data7["message"]["sources"][0]["title"] == "Introduction to C Arrays"
        assert data7["message"]["sources"][0]["location"] == "Page 1"
