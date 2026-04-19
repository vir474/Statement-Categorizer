"""Factory — returns the correct storage backend based on STORAGE_BACKEND env var."""

from app.core.config import settings
from app.services.storage.base import AbstractStorage


def get_storage() -> AbstractStorage:
    if settings.storage_backend == "s3":
        from app.services.storage.s3_storage import S3Storage
        return S3Storage()
    from app.services.storage.local_storage import LocalStorage
    return LocalStorage()
