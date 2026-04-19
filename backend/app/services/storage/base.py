"""Abstract file storage interface — local and S3 implementations both satisfy this."""

from abc import ABC, abstractmethod
from pathlib import Path


class AbstractStorage(ABC):
    @abstractmethod
    async def save(self, file_bytes: bytes, filename: str) -> str:
        """Persist file bytes and return the storage key/path used to retrieve it."""

    @abstractmethod
    async def get_path(self, storage_key: str) -> Path:
        """
        Return a local filesystem Path to the file.
        For S3, this means downloading to a temp file first.
        """

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        """Remove the file from storage."""
