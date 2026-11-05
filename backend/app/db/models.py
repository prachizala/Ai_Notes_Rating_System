"""
SQLAlchemy Models for NoteIQ
"""

import uuid
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, GUID, TimestampMixin

# Safe import for Vector type
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # fallback for environments without pgvector installed


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="student", nullable=False)  # 'student' | 'faculty'
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="uploader", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Stream(Base, TimestampMixin):
    __tablename__ = "streams"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="stream")


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # 1 to 6
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # 'active' | 'coming_soon'

    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="semester")


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("stream_id", "semester_id", "normalized_name", name="uq_subject_stream_sem_norm_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    stream_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("streams.id", ondelete="CASCADE"), nullable=False)
    semester_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    stream: Mapped["Stream"] = relationship("Stream", back_populates="subjects")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="subjects")
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    syllabus_topics: Mapped[List["SyllabusTopic"]] = relationship("SyllabusTopic", back_populates="subject", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="subject", cascade="all, delete-orphan")


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("subject_id", "normalized_name", name="uq_topic_subject_norm_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="topics")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="topic")


class SyllabusTopic(Base, TimestampMixin):
    __tablename__ = "syllabus_topics"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    added_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="syllabus_topics")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, pptx
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)  # queued | processing | complete | failed
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    uploader: Mapped["User"] = relationship("User", back_populates="documents")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="documents")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="documents")
    analyses: Mapped[List["DocumentAnalysis"]] = relationship("DocumentAnalysis", back_populates="document", cascade="all, delete-orphan", order_by="desc(DocumentAnalysis.version)")
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="document", cascade="all, delete-orphan")
    flags: Mapped[List["Flag"]] = relationship("Flag", back_populates="document", cascade="all, delete-orphan")


class DocumentAnalysis(Base, TimestampMixin):
    __tablename__ = "document_analyses"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    rubric_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    topic_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_score: Mapped[float] = mapped_column(Float, nullable=False)
    depth_score: Mapped[float] = mapped_column(Float, nullable=False)
    examples_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score_raw: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score_display: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low | medium | high
    confidence_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    total_topics: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="analyses")
    topics: Mapped[List["AnalysisTopic"]] = relationship("AnalysisTopic", back_populates="analysis", cascade="all, delete-orphan")
    feedback: Mapped[List["AnalysisFeedback"]] = relationship("AnalysisFeedback", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisTopic(Base, TimestampMixin):
    __tablename__ = "analysis_topics"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("document_analyses.id", ondelete="CASCADE"), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(150), nullable=False)
    matched_syllabus_topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("syllabus_topics.id", ondelete="SET NULL"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    analysis: Mapped["DocumentAnalysis"] = relationship("DocumentAnalysis", back_populates="topics")


class AnalysisFeedback(Base, TimestampMixin):
    __tablename__ = "analysis_feedback"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("document_analyses.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)  # strength | improvement | missing_concept | error_found
    text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    analysis: Mapped["DocumentAnalysis"] = relationship("DocumentAnalysis", back_populates="feedback")


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)  # Page 3 or Slide 7
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # pgvector embedding: 768 dimensions default (matching Gemini text-embedding-004)
    # On PostgreSQL, use Vector(768). On fallback SQLite, use Text.
    if Vector is not None:
        embedding = mapped_column(Text().with_variant(Vector(768), "postgresql"), nullable=True)
    else:
        embedding = mapped_column(Text, nullable=True)

    # Full-text search tsvector (PostgreSQL specific, fallback Text on SQLite)
    tsv = mapped_column(Text().with_variant(TSVECTOR, "postgresql"), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")


# Table indexes for chunks
Index("ix_chunks_document_id", DocumentChunk.document_id)


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("document_id", "user_id", name="uq_review_doc_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="New Chat Session", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


class Flag(Base, TimestampMixin):
    __tablename__ = "flags"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    reporter_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending | resolved | dismissed

    document: Mapped["Document"] = relationship("Document", back_populates="flags")
    reporter: Mapped["User"] = relationship("User")
