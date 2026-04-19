"""Category and rule management endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep
from app.crud import categories as crud
from app.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryRuleCreate,
    CategoryRuleRead,
    CategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def list_categories(session: SessionDep):
    return await crud.get_all(session)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, session: SessionDep):
    return await crud.create(session, data, is_user_defined=True)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, data: CategoryUpdate, session: SessionDep):
    category = await crud.get_by_id(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return await crud.update(session, category, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: SessionDep):
    category = await crud.get_by_id(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await crud.delete(session, category)


# ── Rules ──────────────────────────────────────────────────────────────────────

@router.get("/{category_id}/rules", response_model=list[CategoryRuleRead])
async def list_rules(category_id: int, session: SessionDep):
    category = await crud.get_by_id(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return await crud.get_rules(session, category_id)


@router.post("/{category_id}/rules", response_model=CategoryRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(category_id: int, data: CategoryRuleCreate, session: SessionDep):
    category = await crud.get_by_id(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    data.category_id = category_id
    return await crud.create_rule(session, data)


@router.delete("/{category_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(category_id: int, rule_id: int, session: SessionDep):
    from app.models.category import CategoryRule
    rule = await session.get(CategoryRule, rule_id)
    if not rule or rule.category_id != category_id:
        raise HTTPException(status_code=404, detail="Rule not found")
    await crud.delete_rule(session, rule)
