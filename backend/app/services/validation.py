"""
File validation service: magic bytes, MIME types, macro detection, encryption checks, checksum.
"""

import hashlib
import io
import zipfile
from typing import Tuple
import fitz  # PyMuPDF

from app.core.config import settings

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx"}

MIME_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


class FileValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def compute_sha256(content: bytes) -> str:
    """Computes SHA-256 checksum of file bytes."""
    return hashlib.sha256(content).hexdigest()


def validate_uploaded_file(filename: str, content: bytes) -> Tuple[str, str, int]:
    """
    Validates file extension, magic bytes, macro-free status, encryption, and size limit.
    Returns (cleaned_extension, mime_type, file_size).
    Raises FileValidationError on failure.
    """
    # 1. Size check
    file_size = len(content)
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if file_size > max_bytes:
        raise FileValidationError(
            f"File size exceeds maximum limit of {settings.MAX_UPLOAD_MB}MB (received {file_size / (1024*1024):.1f}MB)."
        )
    if file_size < 100:
        raise FileValidationError("File is empty or corrupted (under 100 bytes).")

    # 2. Extension check
    parts = filename.rsplit(".", 1)
    if len(parts) < 2:
        raise FileValidationError("File name must have an extension (.pdf, .docx, or .pptx).")
    ext = parts[1].lower().strip()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file format '.{ext}'. Allowed formats are: PDF, DOCX, and PPTX."
        )

    # 3. Magic bytes and integrity check
    if ext == "pdf":
        if not content.startswith(b"%PDF-"):
            raise FileValidationError("Invalid PDF: missing '%PDF-' header signature.")
        # Check encryption using PyMuPDF
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            if doc.is_encrypted:
                doc.close()
                raise FileValidationError("Encrypted or password-protected PDF files are not supported.")
            doc.close()
        except fitz.FileDataError:
            raise FileValidationError("Corrupted or unreadable PDF file.")

    elif ext in ("docx", "pptx"):
        # Must be valid ZIP archive
        if not content.startswith(b"PK\x03\x04"):
            raise FileValidationError(f"Invalid {ext.upper()}: not a valid OpenXML package.")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # Check for encryption (encrypted zip entries)
                for zinfo in zf.infolist():
                    if zinfo.flag_bits & 0x1:
                        raise FileValidationError(f"Encrypted or password-protected {ext.upper()} files are not supported.")
                    # Reject VBA macros
                    if "vbaProject.bin" in zinfo.filename or zinfo.filename.endswith(".bin"):
                        raise FileValidationError(
                            f"Macro-enabled {ext.upper()} files are not permitted for security reasons."
                        )

                names = set(zf.namelist())
                if ext == "docx":
                    if "word/document.xml" not in names:
                        raise FileValidationError("Invalid DOCX: missing 'word/document.xml'.")
                elif ext == "pptx":
                    if "ppt/presentation.xml" not in names:
                        raise FileValidationError("Invalid PPTX: missing 'ppt/presentation.xml'.")
        except zipfile.BadZipFile:
            raise FileValidationError(f"Corrupted or invalid {ext.upper()} archive.")

    mime_type = MIME_MAP[ext]
    return ext, mime_type, file_size
