"""DB operations for transactions."""

from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionUpdate


async def get_by_id(session: AsyncSession, txn_id: int) -> Optional[Transaction]:
    return await session.get(Transaction, txn_id)


async def list_transactions(
    session: AsyncSession,
    statement_id: Optional[int] = None,
    category_id: Optional[int] = None,
    uncategorized_only: bool = False,
    month: Optional[str] = None,   # "YYYY-MM"
    search: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
) -> list[Transaction]:
    query = select(Transaction)

    if statement_id is not None:
        query = query.where(Transaction.statement_id == statement_id)
    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)
    if uncategorized_only:
        query = query.where(Transaction.category_id.is_(None))  # type: ignore[union-attr]
    if month:
        year, mo = month.split("-")
        query = query.where(
            Transaction.date >= f"{year}-{mo}-01",
            Transaction.date < f"{year}-{int(mo)+1:02d}-01" if int(mo) < 12 else f"{int(year)+1}-01-01",
        )
    if search:
        term = f"%{search}%"
        query = query.where(
            Transaction.description.ilike(term) | Transaction.merchant.ilike(term)  # type: ignore[union-attr]
        )

    query = query.order_by(Transaction.date.desc()).offset(offset).limit(limit)  # type: ignore[union-attr]
    return list((await session.exec(query)).all())


async def update(session: AsyncSession, txn: Transaction, data: TransactionUpdate) -> Transaction:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    # Track that the user manually changed the category
    if "category_id" in data.model_dump(exclude_unset=True):
        txn.categorization_source = "manual"
    session.add(txn)
    await session.commit()
    await session.refresh(txn)
    return txn


async def bulk_insert(session: AsyncSession, transactions: list[Transaction]) -> None:
    for txn in transactions:
        session.add(txn)
    await session.commit()
