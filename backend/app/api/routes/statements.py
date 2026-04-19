"""
Statement upload and management endpoints.
Upload → save file → parse in background → auto-categorize transactions.
"""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app import crud
from app.api.deps import SessionDep, StorageDep
from app.models.models import Statement, Transaction
from app.schemas.statement import StatementRead, StatementUpdate
from app.services.categorizer import categorize_transaction
from app.services.parser import parse_statement
from app.services.storage.base import AbstractStorage

router = APIRouter(prefix="/statements", tags=["statements"])

_ALLOWED_EXTENSIONS = {".pdf", ".csv", ".tsv", ".ofx", ".qfx"}


@router.get("/", response_model=list[StatementRead])
async def list_statements(session: SessionDep):
    rows = await crud.statements.get_all(session)
    results = []
    for stmt, count in rows:
        data = StatementRead.model_validate(stmt)
        data.transaction_count = count
        results.append(data)
    return results


@router.post("/upload", response_model=StatementRead, status_code=status.HTTP_201_CREATED)
async def upload_statement(
    file: UploadFile,
    session: SessionDep,
    storage: StorageDep,
    background_tasks: BackgroundTasks,
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    storage_key = await storage.save(file_bytes, file.filename or "statement")

    statement = Statement(
        filename=file.filename or "statement",
        storage_path=storage_key,
        file_format=suffix.lstrip("."),
        parse_status="pending",
    )
    statement = await crud.statements.create(session, statement)

    # Parse and categorize in the background so upload returns immediately
    background_tasks.add_task(_parse_and_categorize, statement.id, storage_key, storage)

    return StatementRead.model_validate(statement)


@router.get("/{statement_id}", response_model=StatementRead)
async def get_statement(statement_id: int, session: SessionDep):
    stmt = await crud.statements.get_by_id(session, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    return StatementRead.model_validate(stmt)


@router.patch("/{statement_id}", response_model=StatementRead)
async def update_statement(statement_id: int, data: StatementUpdate, session: SessionDep):
    stmt = await crud.statements.get_by_id(session, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(stmt, field, value)
    session.add(stmt)
    await session.commit()
    await session.refresh(stmt)
    return StatementRead.model_validate(stmt)


@router.delete("/{statement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_statement(statement_id: int, session: SessionDep, storage: StorageDep):
    stmt = await crud.statements.get_by_id(session, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    await storage.delete(stmt.storage_path)
    await session.delete(stmt)
    await session.commit()


async def _parse_and_categorize(
    statement_id: int,
    storage_key: str,
    storage: AbstractStorage,
) -> None:
    """Background task: gets its own DB session, parses the file, and categorizes transactions."""
    from app.core.db import get_session as _get_session

    async for bg_session in _get_session():
        stmt = await crud.statements.get_by_id(bg_session, statement_id)
        if not stmt:
            return

        await crud.statements.set_status(bg_session, stmt, "parsing")

        try:
            file_path = await storage.get_path(storage_key)
            result = parse_statement(file_path)
        except Exception as exc:
            await crud.statements.set_status(bg_session, stmt, "error", str(exc))
            return

        await crud.statements.update_period(
            bg_session, stmt, result.period_start, result.period_end, result.account_hint
        )

        all_categories = await crud.categories.get_all(bg_session)
        category_names = [c.name for c in all_categories]
        category_map = {c.name: c.id for c in all_categories}

        transactions_to_insert = []
        for parsed in result.transactions:
            suggestion = await categorize_transaction(
                parsed.description, parsed.merchant, category_names, bg_session
            )
            category_id = category_map.get(suggestion.category_name) if suggestion else None

            transactions_to_insert.append(Transaction(
                statement_id=statement_id,
                date=parsed.date,
                description=parsed.description,
                merchant=parsed.merchant,
                amount=parsed.amount,
                currency=parsed.currency,
                raw_text=parsed.raw_text,
                category_id=category_id,
                categorization_source=suggestion.source if suggestion else "uncategorized",
            ))

        await crud.transactions.bulk_insert(bg_session, transactions_to_insert)
        await crud.statements.set_status(bg_session, stmt, "done")
        break
