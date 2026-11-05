import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models import Stream, Semester, Subject, Topic, Document, User
from app.core.security import hash_password, create_access_token


@pytest.fixture
async def phase7_db():
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
        bca = Stream(name="BCA", slug="bca")
        sem1 = Semester(number=1, status="active")
        session.add_all([bca, sem1])

        faculty = User(name="Prof Alan", email="alan@college.edu", password_hash=hash_password("Pass1234"), role="faculty")
        student = User(name="Charlie", email="charlie@college.edu", password_hash=hash_password("Pass1234"), role="student")
        mod = User(name="Mod Sarah", email="mod@college.edu", password_hash=hash_password("Pass1234"), role="student", is_moderator=True)
        session.add_all([faculty, student, mod])
        await session.commit()

        subj = Subject(stream_id=bca.id, semester_id=sem1.id, name="Python Programming", normalized_name="python programming")
        session.add(subj)
        await session.commit()

        top = Topic(subject_id=subj.id, name="Decorators", normalized_name="decorators")
        session.add(top)
        await session.commit()

        doc = Document(
            subject_id=subj.id,
            topic_id=top.id,
            uploader_id=faculty.id,
            title="Mastering Python Decorators",
            description="Deep dive into functional closures and decorators.",
            file_key="keys/decorators.pdf",
            original_filename="decorators.pdf",
            file_type="pdf",
            file_size=2048,
            checksum_sha256="sha256dummy123",
            status="complete",
        )
        session.add(doc)
        await session.commit()

        yield {
            "faculty_id": str(faculty.id),
            "student_id": str(student.id),
            "mod_id": str(mod.id),
            "subject_id": str(subj.id),
            "doc_id": str(doc.id),
        }

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.anyio
async def test_reviews_upsert_and_isolation(phase7_db):
    doc_id = phase7_db["doc_id"]
    student_id = phase7_db["student_id"]
    token = create_access_token(subject=student_id, role="student")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", token)

        # 1. Submit review
        res1 = await client.put(f"/api/v1/documents/{doc_id}/reviews", json={"stars": 5, "comment": "Brilliant notes!"})
        assert res1.status_code == 200
        assert res1.json()["stars"] == 5

        # 2. Update review (upsert test - should not create duplicate)
        res2 = await client.put(f"/api/v1/documents/{doc_id}/reviews", json={"stars": 4, "comment": "Revised: Good notes."})
        assert res2.status_code == 200
        assert res2.json()["stars"] == 4

        # 3. List reviews - should only be 1 review
        res_list = await client.get(f"/api/v1/documents/{doc_id}/reviews")
        assert res_list.status_code == 200
        reviews = res_list.json()
        assert len(reviews) == 1
        assert reviews[0]["stars"] == 4
        assert reviews[0]["user_name"] == "Charlie"


@pytest.mark.anyio
async def test_search_and_stats(phase7_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search for "python"
        res_s = await client.get("/api/v1/search?q=python")
        assert res_s.status_code == 200
        data = res_s.json()
        assert len(data["documents"]) >= 1
        assert len(data["subjects"]) >= 1

        # Check stats
        res_stats = await client.get("/api/v1/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["total_notes"] == 1
        assert stats["total_subjects"] == 1
        assert stats["total_topics"] == 1
        assert stats["total_contributors"] == 1


@pytest.mark.anyio
async def test_syllabus_faculty_permission(phase7_db):
    subject_id = phase7_db["subject_id"]
    student_id = phase7_db["student_id"]
    faculty_id = phase7_db["faculty_id"]

    student_token = create_access_token(subject=student_id, role="student")
    faculty_token = create_access_token(subject=faculty_id, role="faculty")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Student cannot edit syllabus checklist -> 403 Forbidden
        client.cookies.set("access_token", student_token)
        res_forbid = await client.put(
            f"/api/v1/subjects/{subject_id}/syllabus",
            json={"topics": ["Closures", "Decorators", "Generators"]},
        )
        assert res_forbid.status_code == 403

        # Faculty can edit checklist -> 200 OK
        client.cookies.set("access_token", faculty_token)
        res_ok = await client.put(
            f"/api/v1/subjects/{subject_id}/syllabus",
            json={"topics": ["Closures", "Decorators", "Generators"]},
        )
        assert res_ok.status_code == 200
        assert len(res_ok.json()["topics"]) == 3

        # Get checklist
        res_get = await client.get(f"/api/v1/subjects/{subject_id}/syllabus")
        assert res_get.status_code == 200
        assert "Generators" in res_get.json()["topics"]


@pytest.mark.anyio
async def test_flagging_and_moderation(phase7_db):
    doc_id = phase7_db["doc_id"]
    student_id = phase7_db["student_id"]
    mod_id = phase7_db["mod_id"]

    student_token = create_access_token(subject=student_id, role="student")
    mod_token = create_access_token(subject=mod_id, role="student")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Student flags document
        client.cookies.set("access_token", student_token)
        res_flag = await client.post(
            f"/api/v1/documents/{doc_id}/flag",
            json={"reason": "Contains copyrighted textbook scan."},
        )
        assert res_flag.status_code == 200

        # 2. Student cannot access moderation endpoint -> 403 Forbidden
        res_mod_denied = await client.get("/api/v1/moderation/flags")
        assert res_mod_denied.status_code == 403

        # 3. Moderator can list flags
        client.cookies.set("access_token", mod_token)
        res_mod_ok = await client.get("/api/v1/moderation/flags")
        assert res_mod_ok.status_code == 200
        items = res_mod_ok.json()["items"]
        assert len(items) >= 1
        flag_id = items[0]["id"]

        # 4. Moderator dismisses flag
        res_action = await client.post(
            f"/api/v1/moderation/flags/{flag_id}",
            json={"action": "dismiss"},
        )
        assert res_action.status_code == 200
