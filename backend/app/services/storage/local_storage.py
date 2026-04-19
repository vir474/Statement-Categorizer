"""
Local filesystem storage — default for offline use.
Files are stored under STORAGE_LOCAL_PATH (default: ./data/uploads/).
Uses pathlib.Path throughout to stay cross-platform (Windows / Mac / Linux).
"""

import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings
from app.services.storage.base import AbstractStorage


class LocalStorage(AbstractStorage):
    def __init__(self) -> None:
        # Resolve once at startup — relative to the backend working directory
        self._base: Path = Path(settings.storage_local_path).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    async def save(self, file_bytes: bytes, filename: str) -> str:
        # Prefix with UUID to avoid collisions and path traversal
        safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
        dest = self._base / safe_name
        async with aiofiles.open(dest, "wb") as f:
            await f.write(file_bytes)
        # Return relative key so it's portable when base path changes
        return safe_name

    async def get_path(self, storage_key: str) -> Path:
        return self._base / storage_key

    async def delete(self, storage_key: str) -> None:
        target = self._base / storage_key
        if target.exists():
            target.unlink()
