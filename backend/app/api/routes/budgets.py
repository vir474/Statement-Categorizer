"""Monthly budget summary endpoint."""

from decimal import Decimal

from fastapi import APIRouter, Query
from sqlmodel import func, select

from app.api.deps import SessionDep
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.budget import BudgetSummary, CategorySpend

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("/summary", response_model=BudgetSummary)
async def get_monthly_summary(
    session: SessionDep,
    month: str = Query(..., description="YYYY-MM format, e.g. 2024-01"),
):
    """
    Return total spend, income, net, and per-category breakdown for a given month.
    Income = transactions with negative amounts (credits/refunds).
    Spend  = transactions with positive amounts (debits/charges).
    """
    try:
        year_str, month_str = month.split("-")
        year, mo = int(year_str), int(month_str)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="month must be YYYY-MM format")

    # Inclusive start, exclusive end for the month
    start = f"{year}-{mo:02d}-01"
    end = f"{year}-{mo+1:02d}-01" if mo < 12 else f"{year+1}-01-01"

    # Aggregate spend per category with a single query
    rows = (await session.exec(
        select(
            Transaction.category_id,
            Category.name.label("category_name"),        # type: ignore[union-attr]
            Category.parent_id,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("txn_count"),
        )
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(Transaction.date >= start, Transaction.date < end)
        .group_by(Transaction.category_id, Category.name, Category.parent_id)
    )).all()

    # Resolve parent category names
    all_cats = {c.id: c for c in (await session.exec(select(Category))).all()}

    by_category: list[CategorySpend] = []
    total_spend = Decimal(0)
    total_income = Decimal(0)

    for row in rows:
        total = Decimal(str(row.total or 0))
        parent_name: str | None = None
        if row.parent_id and row.parent_id in all_cats:
            parent_name = all_cats[row.parent_id].name

        by_category.append(CategorySpend(
            category_id=row.category_id,
            category_name=row.category_name or "Uncategorized",
            parent_category_name=parent_name,
            total=total,
            transaction_count=row.txn_count,
        ))

        if total > 0:
            total_spend += total
        else:
            total_income += abs(total)

    by_category.sort(key=lambda c: c.total, reverse=True)

    return BudgetSummary(
        month=month,
        total_spend=total_spend,
        total_income=total_income,
        net=total_income - total_spend,
        by_category=by_category,
    )


@router.get("/months", response_model=list[str])
async def list_available_months(session: SessionDep):
    """Return all months that have at least one transaction, sorted descending."""
    rows = (await session.exec(
        select(func.strftime("%Y-%m", Transaction.date).label("month"))
        .distinct()
        .order_by(func.strftime("%Y-%m", Transaction.date).desc())
    )).all()
    return [r for r in rows if r]
