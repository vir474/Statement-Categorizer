"""DB operations for statements."""

from typing import Optional

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.statement import Statement
from app.models.transaction import Transaction


async def get_all(session: AsyncSession) -> list[tuple[Statement, int]]:
    """Return all statements with their transaction counts."""
    rows = (await session.exec(
        select(Statement, func.count(Transaction.id).label("count"))
        .outerjoin(Transaction, Transaction.statement_id == Statement.id)
        .group_by(Statement.id)
        .order_by(Statement.uploaded_at.desc())  # type: ignore[union-attr]
    )).all()
    return list(rows)


async def get_by_id(session: AsyncSession, statement_id: int) -> Optional[Statement]:
    return await session.get(Statement, statement_id)


async def create(session: AsyncSession, statement: Statement) -> Statement:
    session.add(statement)
    await session.commit()
    await session.refresh(statement)
    return statement


async def set_status(
    session: AsyncSession,
    statement: Statement,
    status: str,
    error: Optional[str] = None,
) -> Statement:
    statement.parse_status = status
    statement.parse_error = error
    session.add(statement)
    await session.commit()
    await session.refresh(statement)
    return statement


async def update_period(
    session: AsyncSession,
    statement: Statement,
    period_start,
    period_end,
    account_hint: Optional[str] = None,
) -> Statement:
    statement.period_start = period_start
    statement.period_end = period_end
    if account_hint and not statement.account_name:
        statement.account_name = account_hint
    session.add(statement)
    await session.commit()
    await session.refresh(statement)
    return statement
