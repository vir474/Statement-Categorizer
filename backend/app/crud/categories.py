"""DB operations for categories and rules — no business logic here."""

from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.category import Category, CategoryRule
from app.schemas.category import CategoryCreate, CategoryRuleCreate, CategoryUpdate


async def get_all(session: AsyncSession) -> list[Category]:
    return list((await session.exec(select(Category))).all())


async def get_by_id(session: AsyncSession, category_id: int) -> Optional[Category]:
    return await session.get(Category, category_id)


async def get_by_name(session: AsyncSession, name: str) -> Optional[Category]:
    return (await session.exec(select(Category).where(Category.name == name))).first()


async def create(session: AsyncSession, data: CategoryCreate, is_user_defined: bool = True) -> Category:
    category = Category(**data.model_dump(), is_user_defined=is_user_defined)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def update(session: AsyncSession, category: Category, data: CategoryUpdate) -> Category:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def delete(session: AsyncSession, category: Category) -> None:
    await session.delete(category)
    await session.commit()


async def get_rules(session: AsyncSession, category_id: int) -> list[CategoryRule]:
    return list((await session.exec(
        select(CategoryRule).where(CategoryRule.category_id == category_id)
    )).all())


async def create_rule(session: AsyncSession, data: CategoryRuleCreate) -> CategoryRule:
    rule = CategoryRule(**data.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def delete_rule(session: AsyncSession, rule: CategoryRule) -> None:
    await session.delete(rule)
    await session.commit()
