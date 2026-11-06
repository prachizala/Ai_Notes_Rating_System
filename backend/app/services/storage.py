"""
S3-Compatible Object Storage Service (AWS S3, MinIO, Cloudflare R2).
Includes fallback to local storage directory for local testing without active MinIO.
"""

import os
import io
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import BinaryIO, Optional

from app.core.config import settings
from app.core.logging import logger

LOCAL_STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage_uploads"))


class StorageService:
    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.use_s3 = False
        self.s3_client = None

        if settings.ENVIRONMENT in ("test", "development") or os.environ.get("ENVIRONMENT") in ("test", "development"):
            # Check if S3_ENDPOINT_URL is local MinIO and not reachable
            self.use_s3 = False
            os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
            return

        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                    connect_timeout=1.0,
                    read_timeout=1.0,
                    retries={"max_attempts": 1},
                ),
            )
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket)
            self.use_s3 = True
            logger.info(f"Connected to S3 storage bucket: {self.bucket}")
        except Exception as e:
            logger.warning(f"S3 storage unavailable ({e}). Using local fallback storage at: {LOCAL_STORAGE_DIR}")
            os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
            self.use_s3 = False

    def upload_file(self, file_obj: BinaryIO, file_key: str, content_type: str) -> str:
        """Uploads a file object to S3 or local fallback."""
        file_obj.seek(0)
        if self.use_s3 and self.s3_client:
            try:
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket,
                    file_key,
                    ExtraArgs={"ContentType": content_type},
                )
                return file_key
            except Exception as e:
                logger.error(f"S3 upload error: {e}. Falling back to local storage.")

        # Local storage fallback
        dest_path = os.path.join(LOCAL_STORAGE_DIR, file_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        file_obj.seek(0)
        with open(dest_path, "wb") as f:
            f.write(file_obj.read())
        return file_key

    def download_file_bytes(self, file_key: str) -> bytes:
        """Downloads file contents as bytes."""
        if self.use_s3 and self.s3_client:
            try:
                buffer = io.BytesIO()
                self.s3_client.download_fileobj(self.bucket, file_key, buffer)
                buffer.seek(0)
                return buffer.read()
            except Exception as e:
                logger.error(f"S3 download error: {e}. Trying local fallback.")

        dest_path = os.path.join(LOCAL_STORAGE_DIR, file_key)
        if os.path.exists(dest_path):
            with open(dest_path, "rb") as f:
                return f.read()
        raise FileNotFoundError(f"File key '{file_key}' not found in storage.")

    def generate_presigned_download_url(self, file_key: str, original_filename: str) -> str:
        """Generates a secure temporary download URL."""
        if self.use_s3 and self.s3_client:
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": file_key,
                        "ResponseContentDisposition": f'attachment; filename="{original_filename}"',
                    },
                    ExpiresIn=settings.SIGNED_URL_EXPIRE_SECONDS,
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate presigned S3 url: {e}")

        # Fallback local direct route
        return f"{settings.BACKEND_URL}/api/v1/documents/raw/{file_key}?filename={original_filename}"

    def delete_file(self, file_key: str) -> bool:
        """Deletes a file from storage."""
        if self.use_s3 and self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=self.bucket, Key=file_key)
            except Exception as e:
                logger.error(f"Failed to delete S3 file {file_key}: {e}")

        dest_path = os.path.join(LOCAL_STORAGE_DIR, file_key)
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return True


storage_service = StorageService()
