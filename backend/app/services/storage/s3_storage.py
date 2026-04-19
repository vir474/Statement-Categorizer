"""
S3 / Cloudflare R2 storage — used when STORAGE_BACKEND=s3.
Boto3 is the only new dependency; everything else stays the same.
"""

import tempfile
import uuid
from pathlib import Path

import boto3

from app.core.config import settings
from app.services.storage.base import AbstractStorage


class S3Storage(AbstractStorage):
    def __init__(self) -> None:
        kwargs: dict = {
            "region_name": settings.s3_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
        # endpoint_url is only set for R2 / MinIO — leave empty for standard AWS
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.s3_bucket

    async def save(self, file_bytes: bytes, filename: str) -> str:
        key = f"uploads/{uuid.uuid4().hex}_{Path(filename).name}"
        self._client.put_object(Bucket=self._bucket, Key=key, Body=file_bytes)
        return key

    async def get_path(self, storage_key: str) -> Path:
        # Download to a named temp file — caller is responsible for cleanup
        suffix = Path(storage_key).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        self._client.download_fileobj(self._bucket, storage_key, tmp)
        tmp.flush()
        return Path(tmp.name)

    async def delete(self, storage_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=storage_key)
