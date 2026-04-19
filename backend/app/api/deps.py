"""Shared FastAPI dependencies injected via Depends()."""

from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.services.storage import get_storage
from app.services.storage.base import AbstractStorage

# Type aliases for cleaner route signatures
SessionDep = Annotated[AsyncSession, Depends(get_session)]
StorageDep = Annotated[AbstractStorage, Depends(get_storage)]
