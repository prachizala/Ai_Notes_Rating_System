import pytest
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import User, Stream, Semester, Subject, Topic, Document, Review
from app.core.normalizer import normalize_name


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_user_creation_and_unique_email(db_session):
    u1 = User(
        name="Alice Student",
        email="alice@example.com",
        password_hash="argon2hash...",
        role="student"
    )
    db_session.add(u1)
    db_session.commit()

    assert u1.id is not None
    assert u1.role == "student"
    assert not u1.is_moderator

    # Duplicate email should fail
    u2 = User(
        name="Alice Fake",
        email="alice@example.com",
        password_hash="anotherhash",
        role="student"
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_subject_and_topic_normalization_and_uniqueness(db_session):
    stream = Stream(name="Bachelor of Computer Applications", slug="bca")
    semester = Semester(number=1, status="active")
    user = User(name="Prof Smith", email="smith@example.com", password_hash="hash", role="faculty")
    db_session.add_all([stream, semester, user])
    db_session.commit()

    subj_name = "C Programming"
    norm_name = normalize_name(subj_name)
    subject = Subject(
        stream_id=stream.id,
        semester_id=semester.id,
        name=subj_name,
        normalized_name=norm_name,
        created_by=user.id
    )
    db_session.add(subject)
    db_session.commit()

    # Duplicate normalized name for same stream and semester should violate constraint
    duplicate_subj = Subject(
        stream_id=stream.id,
        semester_id=semester.id,
        name="c  programming!!",
        normalized_name=normalize_name("c  programming!!"),
        created_by=user.id
    )
    db_session.add(duplicate_subj)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_review_one_per_user_per_document(db_session):
    stream = Stream(name="BBA", slug="bba")
    sem = Semester(number=2, status="active")
    user = User(name="John", email="john@example.com", password_hash="hash", role="student")
    db_session.add_all([stream, sem, user])
    db_session.commit()

    subject = Subject(stream_id=stream.id, semester_id=sem.id, name="Marketing", normalized_name="marketing")
    topic = Topic(subject_id=subject.id, name="Segmentation", normalized_name="segmentation")
    subject.topics.append(topic)
    db_session.add(subject)
    db_session.commit()

    doc = Document(
        subject_id=subject.id,
        topic_id=topic.id,
        uploader_id=user.id,
        title="Marketing Principles 101",
        file_key="keys/test.pdf",
        original_filename="marketing.pdf",
        file_type="pdf",
        file_size=1024,
        checksum_sha256="abc123456",
        status="complete"
    )
    db_session.add(doc)
    db_session.commit()

    r1 = Review(document_id=doc.id, user_id=user.id, stars=5, comment="Great notes!")
    db_session.add(r1)
    db_session.commit()

    r2 = Review(document_id=doc.id, user_id=user.id, stars=4, comment="Duplicate attempt")
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
