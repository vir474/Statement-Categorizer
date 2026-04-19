"""Transaction listing, editing, and bulk re-categorization endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import SessionDep
from app.crud import categories as categories_crud
from app.crud import transactions as txn_crud
from app.schemas.transaction import TransactionBulkCategorize, TransactionRead, TransactionUpdate
from app.services.categorizer import categorize_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionRead])
async def list_transactions(
    session: SessionDep,
    statement_id: int | None = Query(None),
    category_id: int | None = Query(None),
    uncategorized_only: bool = Query(False),
    month: str | None = Query(None, description="YYYY-MM format"),
    search: str | None = Query(None),
    limit: int = Query(500, le=1000),
    offset: int = Query(0),
):
    txns = await txn_crud.list_transactions(
        session,
        statement_id=statement_id,
        category_id=category_id,
        uncategorized_only=uncategorized_only,
        month=month,
        search=search,
        limit=limit,
        offset=offset,
    )
    return txns


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(transaction_id: int, data: TransactionUpdate, session: SessionDep):
    txn = await txn_crud.get_by_id(session, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return await txn_crud.update(session, txn, data)


@router.post("/recategorize", response_model=list[TransactionRead])
async def bulk_recategorize(data: TransactionBulkCategorize, session: SessionDep):
    """Re-run the categorization pipeline on a set of transactions."""
    all_categories = await categories_crud.get_all(session)
    category_names = [c.name for c in all_categories]
    category_map = {c.name: c.id for c in all_categories}

    results = []
    for txn_id in data.transaction_ids:
        txn = await txn_crud.get_by_id(session, txn_id)
        if not txn:
            continue
        suggestion = await categorize_transaction(
            txn.description, txn.merchant, category_names, session
        )
        update_data = TransactionUpdate(
            category_id=category_map.get(suggestion.category_name) if suggestion else None
        )
        # Preserve 'manual' source — only overwrite rule/llm/uncategorized
        if txn.categorization_source != "manual":
            txn.categorization_source = suggestion.source if suggestion else "uncategorized"
        updated = await txn_crud.update(session, txn, update_data)
        results.append(updated)

    return results
