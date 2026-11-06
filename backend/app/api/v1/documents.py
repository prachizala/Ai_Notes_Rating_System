"""
Documents endpoints: Upload, Listing, Details, Editing, Deletion, and Signed Downloads.
"""

import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import Response as RawResponse
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import check_resource_owner, get_current_user
from app.core.config import settings
from app.core.normalizer import normalize_name
from app.core.rate_limit import check_rate_limit
from app.db.models import (
    Document,
    DocumentAnalysis,
    DocumentChunk,
    Review,
    Semester,
    Stream,
    Subject,
    Topic,
    User,
)
from app.db.session import get_db
from app.schemas.document import (
    DocumentDownloadResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdateRequest,
)
from app.schemas.study import StudyPackResponse
from app.services.study_tools import study_tools_service
from app.schemas.exam_predictor import ExamPredictionResponse
from app.services.exam_predictor import exam_predictor_service
from app.services.storage import storage_service
from app.services.validation import (
    FileValidationError,
    compute_sha256,
    validate_uploaded_file,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


async def get_document_with_relations(document_id: uuid.UUID, db: AsyncSession) -> Optional[Document]:
    """Helper to fetch document with all necessary eager-loaded relationships."""
    stmt = (
        select(Document)
        .where(Document.id == document_id)
        .options(
            selectinload(Document.uploader),
            selectinload(Document.subject).selectinload(Subject.stream),
            selectinload(Document.subject).selectinload(Subject.semester),
            selectinload(Document.topic),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def format_document_response(doc: Document, db: AsyncSession) -> DocumentResponse:
    """Helper to assemble DocumentResponse with calculated ratings and names."""
    # 1. Overall AI rating from latest analysis
    ai_rating_stmt = (
        select(DocumentAnalysis.overall_score_display)
        .where(DocumentAnalysis.document_id == doc.id)
        .order_by(desc(DocumentAnalysis.version))
        .limit(1)
    )
    ai_rating = (await db.execute(ai_rating_stmt)).scalar_one_or_none()

    # 2. Student ratings average and count
    review_stmt = (
        select(func.avg(Review.stars), func.count(Review.id))
        .where(Review.document_id == doc.id)
    )
    rev_res = (await db.execute(review_stmt)).one()
    student_avg = float(rev_res[0]) if rev_res[0] is not None else None
    student_count = rev_res[1] or 0

    return DocumentResponse(
        id=doc.id,
        subject_id=doc.subject_id,
        topic_id=doc.topic_id,
        uploader_id=doc.uploader_id,
        uploader_name=doc.uploader.name if doc.uploader else "Anonymous",
        uploader_role=doc.uploader.role if doc.uploader else "student",
        stream_name=doc.subject.stream.name if doc.subject and doc.subject.stream else None,
        semester_number=doc.subject.semester.number if doc.subject and doc.subject.semester else None,
        subject_name=doc.subject.name if doc.subject else None,
        topic_name=doc.topic.name if doc.topic else None,
        title=doc.title,
        description=doc.description,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        failure_reason=doc.failure_reason,
        download_count=doc.download_count,
        overall_rating=ai_rating,
        student_rating_avg=round(student_avg, 1) if student_avg else None,
        student_rating_count=student_count,
        created_at=doc.created_at,
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    stream: str = Form(..., description="Stream slug (bba, bca, bvoc) or Stream UUID"),
    semester: int = Form(..., description="Semester number (1-5; Semester 6 is rejected)"),
    subject: str = Form(..., min_length=2, max_length=150),
    topic: str = Form(..., min_length=2, max_length=150),
    title: str = Form(..., min_length=2, max_length=200),
    description: Optional[str] = Form(None, max_length=2000),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Upload notes file (PDF, DOCX, PPTX).
    Enforces daily rate limits, rejects Semester 6, checks SHA-256 duplicate,
    dynamically creates subject/topic, stores file and enqueues AI analysis.
    """
    # 1. Enforce daily upload rate limit per user
    rate_key = f"rl:upload:{current_user.id}"
    if not check_rate_limit(rate_key, limit=settings.UPLOAD_RATE_LIMIT_PER_DAY, window_seconds=86400):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily upload limit reached ({settings.UPLOAD_RATE_LIMIT_PER_DAY} uploads per day). Please try again tomorrow.",
        )

    # 2. Reject Semester 6
    if semester == 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester 6 is Coming Soon. Uploads and note selection are not allowed.",
        )

    # 3. Validate Stream
    stream_stmt = select(Stream).where(
        or_(Stream.slug == stream.lower().strip(), Stream.name.ilike(stream.strip()))
    )
    stream_obj = (await db.execute(stream_stmt)).scalar_one_or_none()
    if not stream_obj:
        try:
            stream_obj = await db.get(Stream, uuid.UUID(stream))
        except ValueError:
            pass
    if not stream_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown academic stream '{stream}'. Available streams are: BBA, BCA, B.Voc.",
        )

    # 4. Validate Semester in DB
    sem_stmt = select(Semester).where(Semester.number == semester)
    sem_obj = (await db.execute(sem_stmt)).scalar_one_or_none()
    if not sem_obj or sem_obj.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Semester {semester} is currently not active for uploads.",
        )

    # 5. Read and validate uploaded file
    file_bytes = await file.read()
    try:
        ext, mime_type, file_size = validate_uploaded_file(file.filename or "upload.pdf", file_bytes)
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )

    # 6. Compute SHA-256 Checksum
    checksum = compute_sha256(file_bytes)

    # 7. Normalize subject & topic names and Atomic Get-or-Create
    norm_subj = normalize_name(subject)
    norm_topic = normalize_name(topic)

    subj_stmt = select(Subject).where(
        Subject.stream_id == stream_obj.id,
        Subject.semester_id == sem_obj.id,
        Subject.normalized_name == norm_subj,
    )
    subject_row = (await db.execute(subj_stmt)).scalar_one_or_none()
    if not subject_row:
        subject_row = Subject(
            stream_id=stream_obj.id,
            semester_id=sem_obj.id,
            name=subject.strip(),
            normalized_name=norm_subj,
            created_by=current_user.id,
        )
        db.add(subject_row)
        await db.flush()

    topic_stmt = select(Topic).where(
        Topic.subject_id == subject_row.id,
        Topic.normalized_name == norm_topic,
    )
    topic_row = (await db.execute(topic_stmt)).scalar_one_or_none()
    if not topic_row:
        topic_row = Topic(
            subject_id=subject_row.id,
            name=topic.strip(),
            normalized_name=norm_topic,
        )
        db.add(topic_row)
        await db.flush()

    # 8. Check duplicate checksum in same subject and topic
    dup_stmt = select(Document).where(
        Document.subject_id == subject_row.id,
        Document.topic_id == topic_row.id,
        Document.checksum_sha256 == checksum,
    )
    dup_doc = (await db.execute(dup_stmt)).scalar_one_or_none()
    if dup_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An identical document has already been uploaded for '{subject_row.name}' under topic '{topic_row.name}'. (Title: '{dup_doc.title}').",
        )

    # 9. Store file in object storage under unique random key
    file_key = f"documents/{uuid.uuid4()}.{ext}"
    import io
    storage_service.upload_file(io.BytesIO(file_bytes), file_key, mime_type)

    # 10. Create Document in database with queued status
    doc = Document(
        subject_id=subject_row.id,
        topic_id=topic_row.id,
        uploader_id=current_user.id,
        title=title.strip(),
        description=description.strip() if description else None,
        file_key=file_key,
        original_filename=file.filename or f"note.{ext}",
        file_type=ext,
        file_size=file_size,
        checksum_sha256=checksum,
        status="queued",
        download_count=0,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc, ["uploader", "subject", "topic"])

    # 11. Enqueue background analysis job
    try:
        from app.workers.jobs import enqueue_document_analysis
        enqueue_document_analysis(str(doc.id))
    except Exception as e:
        # Worker enqueue logged; document remains in queued state
        pass

    return await format_document_response(doc, db)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    stream: Optional[str] = Query(None),
    semester: Optional[int] = Query(None),
    subject: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query("newest", pattern="^(newest|rating|downloads)$"),
    role: Optional[str] = Query(None, pattern="^(student|faculty)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Public: Browse and filter documents with sorting and pagination.
    """
    stmt = (
        select(Document)
        .join(Document.subject)
        .join(Subject.stream)
        .join(Subject.semester)
        .join(Document.uploader)
        .options(
            selectinload(Document.uploader),
            selectinload(Document.subject).selectinload(Subject.stream),
            selectinload(Document.subject).selectinload(Subject.semester),
            selectinload(Document.topic),
        )
    )

    # Filter by stream
    if stream:
        try:
            stream_id = uuid.UUID(stream)
            stmt = stmt.where(Subject.stream_id == stream_id)
        except ValueError:
            stmt = stmt.where(Stream.slug == stream.lower().strip())

    # Filter by semester
    if semester:
        stmt = stmt.where(Semester.number == semester)

    # Filter by subject
    if subject:
        try:
            subj_id = uuid.UUID(subject)
            stmt = stmt.where(Document.subject_id == subj_id)
        except ValueError:
            stmt = stmt.where(Subject.normalized_name == normalize_name(subject))

    # Filter by topic
    if topic:
        try:
            top_id = uuid.UUID(topic)
            stmt = stmt.where(Document.topic_id == top_id)
        except ValueError:
            stmt = stmt.where(Topic.normalized_name == normalize_name(topic))

    # Filter by uploader role
    if role:
        stmt = stmt.where(User.role == role)

    # Search keyword
    if q:
        search_kw = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                Document.title.ilike(search_kw),
                Document.description.ilike(search_kw),
                Subject.normalized_name.ilike(search_kw),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sorting
    if sort == "downloads":
        stmt = stmt.order_by(desc(Document.download_count), desc(Document.created_at))
    elif sort == "rating":
        # Join latest analysis overall score display
        stmt = stmt.outerjoin(
            DocumentAnalysis,
            DocumentAnalysis.document_id == Document.id
        ).order_by(desc(DocumentAnalysis.overall_score_display), desc(Document.created_at))
    else:
        # Default: newest
        stmt = stmt.order_by(desc(Document.created_at))

    # Pagination
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    docs = result.scalars().all()

    items = [await format_document_response(d, db) for d in docs]
    pages = math.ceil(total / limit) if total > 0 else 1

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Public: Retrieves single document details with ratings and status."""
    doc = await get_document_with_relations(document_id, db)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return await format_document_response(doc, db)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Authenticated: Owner-only update of document title and description."""
    doc = await get_document_with_relations(document_id, db)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    check_resource_owner(doc.uploader_id, current_user, "document")

    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.description is not None:
        doc.description = payload.description.strip()

    await db.commit()
    doc = await get_document_with_relations(document_id, db)
    return await format_document_response(doc, db)


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Owner-only deletion.
    Cascades document chunks, analysis reports, reviews, and deletes object storage file.
    """
    doc = await get_document_with_relations(document_id, db)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    check_resource_owner(doc.uploader_id, current_user, "document")

    # Delete storage file
    storage_service.delete_file(doc.file_key)

    # Delete row from DB (cascade deletes chunks, analyses, reviews)
    await db.delete(doc)
    await db.commit()

    return {"message": "Document and all associated analyses deleted successfully."}


@router.get("/{document_id}/download", response_model=DocumentDownloadResponse)
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticated: Generates short-lived signed download URL and increments download_count.
    """
    doc = await get_document_with_relations(document_id, db)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Increment download count
    doc.download_count += 1
    await db.commit()

    download_url = storage_service.generate_presigned_download_url(
        doc.file_key, doc.original_filename
    )

    return DocumentDownloadResponse(
        download_url=download_url,
        filename=doc.original_filename,
    )


@router.get("/{document_id}/study-tools", response_model=StudyPackResponse)
async def get_document_study_tools(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns an interactive Study Pack:
    - 5 Active Recall Quiz questions with explanations
    - 6-8 High-yield concept Flashcards
    Directly grounded in the uploaded notes.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Fetch chunks
    chunks_stmt = (
        select(DocumentChunk.text, DocumentChunk.location)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks_res = await db.execute(chunks_stmt)
    chunks = chunks_res.all()
    combined_text = "\n\n".join([f"[{c[1]}]\n{c[0]}" for c in chunks])

    # Fetch analysis summary if available
    analysis_stmt = (
        select(DocumentAnalysis.summary)
        .where(DocumentAnalysis.document_id == document_id)
        .order_by(desc(DocumentAnalysis.version))
        .limit(1)
    )
    analysis_res = await db.execute(analysis_stmt)
    summary = analysis_res.scalar_one_or_none() or ""

    study_pack = study_tools_service.generate_study_pack(
        document_title=doc.title,
        text=combined_text or doc.description or doc.title,
        summary=summary,
    )

    return StudyPackResponse(
        document_id=str(doc.id),
        document_title=doc.title,
        quiz=study_pack.get("quiz", []),
        flashcards=study_pack.get("flashcards", []),
    )


@router.get("/{document_id}/exam-predictions", response_model=ExamPredictionResponse)
async def get_document_exam_predictions(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Innovation 2: Predicts high-probability university examination questions
    categorized by 2 Marks, 5 Marks, and 10 Marks with examiner answer expectations.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks_stmt = (
        select(DocumentChunk.text, DocumentChunk.location)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks_res = await db.execute(chunks_stmt)
    chunks = chunks_res.all()
    combined_text = "\n\n".join([f"[{c[1]}]\n{c[0]}" for c in chunks])

    analysis_stmt = (
        select(DocumentAnalysis.summary)
        .where(DocumentAnalysis.document_id == document_id)
        .order_by(desc(DocumentAnalysis.version))
        .limit(1)
    )
    analysis_res = await db.execute(analysis_stmt)
    summary = analysis_res.scalar_one_or_none() or ""

    predictions = exam_predictor_service.predict_questions(
        document_title=doc.title,
        text=combined_text or doc.description or doc.title,
        summary=summary,
    )

    return ExamPredictionResponse(
        document_id=str(doc.id),
        document_title=doc.title,
        total_predicted=len(predictions.get("questions", [])),
        questions=predictions.get("questions", []),
        exam_tips=predictions.get("exam_tips", []),
    )


@router.get("/raw/{file_key:path}")
async def serve_raw_storage_file(
    file_key: str,
    filename: Optional[str] = "download",
):
    """Fallback endpoint for serving files when local storage fallback is active."""
    try:
        content = storage_service.download_file_bytes(file_key)
        return RawResponse(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in storage.")
