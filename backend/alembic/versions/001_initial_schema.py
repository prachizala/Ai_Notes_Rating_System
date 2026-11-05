"""initial schema with pgvector and pg_trgm

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-05 20:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostgreSQL Extensions if running on postgresql
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='student', nullable=False),
        sa.Column('is_moderator', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 3. Streams Table
    op.create_table(
        'streams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_streams_slug', 'streams', ['slug'], unique=True)

    # 4. Semesters Table
    op.create_table(
        'semesters',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_semesters_number', 'semesters', ['number'], unique=True)

    # 5. Subjects Table
    op.create_table(
        'subjects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('stream_id', sa.UUID(), nullable=False),
        sa.Column('semester_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('normalized_name', sa.String(length=150), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stream_id'], ['streams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stream_id', 'semester_id', 'normalized_name', name='uq_subject_stream_sem_norm_name'),
    )
    op.create_index('ix_subjects_normalized_name', 'subjects', ['normalized_name'])

    # 6. Topics Table
    op.create_table(
        'topics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('normalized_name', sa.String(length=150), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subject_id', 'normalized_name', name='uq_topic_subject_norm_name'),
    )
    op.create_index('ix_topics_normalized_name', 'topics', ['normalized_name'])

    # 7. Syllabus Topics Table
    op.create_table(
        'syllabus_topics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('added_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 8. Documents Table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('topic_id', sa.UUID(), nullable=False),
        sa.Column('uploader_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='queued', nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('download_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_key'),
    )
    op.create_index('ix_documents_checksum_sha256', 'documents', ['checksum_sha256'])

    # 9. Document Analyses Table
    op.create_table(
        'document_analyses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('rubric_version', sa.String(length=20), server_default='v1', nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('topic_coverage_pct', sa.Float(), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=False),
        sa.Column('explanation_score', sa.Float(), nullable=False),
        sa.Column('depth_score', sa.Float(), nullable=False),
        sa.Column('examples_score', sa.Float(), nullable=False),
        sa.Column('overall_score_raw', sa.Float(), nullable=False),
        sa.Column('overall_score_display', sa.Float(), nullable=False),
        sa.Column('confidence', sa.String(length=20), server_default='medium', nullable=False),
        sa.Column('confidence_reason', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('total_topics', sa.Integer(), server_default='0', nullable=False),
        sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 10. Analysis Topics Table
    op.create_table(
        'analysis_topics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.Column('topic_name', sa.String(length=150), nullable=False),
        sa.Column('matched_syllabus_topic_id', sa.UUID(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['document_analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_syllabus_topic_id'], ['syllabus_topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 11. Analysis Feedback Table
    op.create_table(
        'analysis_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.Column('kind', sa.String(length=30), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('evidence_ref', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['document_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 12. Document Chunks Table
    if is_postgres:
        op.execute("""
            CREATE TABLE document_chunks (
                id UUID PRIMARY KEY,
                document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                location VARCHAR(100) NOT NULL,
                text TEXT NOT NULL,
                embedding vector(768),
                tsv tsvector,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)
        # HNSW Index for cosine distance
        op.execute("CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);")
        # GIN Index for full-text search
        op.execute("CREATE INDEX idx_chunks_tsv ON document_chunks USING gin (tsv);")
        # Trigram indexes
        op.execute("CREATE INDEX idx_subjects_trgm ON subjects USING gin (name gin_trgm_ops);")
        op.execute("CREATE INDEX idx_topics_trgm ON topics USING gin (name gin_trgm_ops);")
    else:
        op.create_table(
            'document_chunks',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('document_id', sa.UUID(), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False),
            sa.Column('location', sa.String(length=100), nullable=False),
            sa.Column('text', sa.Text(), nullable=False),
            sa.Column('embedding', sa.Text(), nullable=True),
            sa.Column('tsv', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])

    # 13. Reviews Table
    op.create_table(
        'reviews',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'user_id', name='uq_review_doc_user'),
    )

    # 14. Chat Sessions & Messages Table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), server_default='New Chat Session', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources_json', postgresql.JSONB(astext_type=sa.Text()) if is_postgres else sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 15. Flags Table
    op.create_table(
        'flags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('reporter_id', sa.UUID(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('flags')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('reviews')
    op.drop_table('document_chunks')
    op.drop_table('analysis_feedback')
    op.drop_table('analysis_topics')
    op.drop_table('document_analyses')
    op.drop_table('documents')
    op.drop_table('syllabus_topics')
    op.drop_table('topics')
    op.drop_table('subjects')
    op.drop_table('semesters')
    op.drop_table('streams')
    op.drop_table('users')
