"""
FastAPI application entry point.
Registers all routers, configures CORS, and seeds default data on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import budgets, categories, statements, transactions
from app.core.config import settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before serving requests."""
    # Create DB tables (dev mode). In production, Alembic handles migrations.
    await init_db()
    # Seed default categories and rules if the DB is empty
    await _seed_defaults()
    yield


app = FastAPI(
    title="Statement Categorizer",
    description="Bank & credit card statement analyzer with budgeting",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statements.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(budgets.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _seed_defaults() -> None:
    """
    Populate default categories + rules on first run.
    Skips if any categories already exist (idempotent).
    """
    from app.core.db import get_session
    from app.crud.categories import create, create_rule, get_all
    from app.schemas.category import CategoryCreate, CategoryRuleCreate
    from app.services.categorizer.rule_engine import DEFAULT_RULES

    async for session in get_session():
        existing = await get_all(session)
        if existing:
            break  # Already seeded

        # Create top-level categories first
        top_level = {
            "Food & Drink": "#f59e0b",
            "Transportation": "#3b82f6",
            "Shopping": "#8b5cf6",
            "Bills & Utilities": "#ef4444",
            "Health": "#10b981",
            "Finance": "#6b7280",
            "Travel": "#06b6d4",
            "Income": "#22c55e",
            "Other": "#94a3b8",
        }
        parent_map: dict[str, int] = {}
        for name, color in top_level.items():
            cat = await create(session, CategoryCreate(name=name, color=color), is_user_defined=False)
            parent_map[name] = cat.id  # type: ignore[assignment]

        # Sub-categories grouped under parents
        sub_categories = {
            "Food & Drink": [("Groceries", "#f59e0b"), ("Restaurants & Cafes", "#f97316"), ("Dining & Delivery", "#fb923c")],
            "Transportation": [("Rideshare & Transit", "#3b82f6"), ("Gas", "#2563eb")],
            "Shopping": [("Amazon", "#8b5cf6"), ("Big Box Retail", "#7c3aed"), ("Electronics", "#6d28d9")],
            "Bills & Utilities": [("Utilities", "#ef4444"), ("Phone & Internet", "#dc2626"), ("Subscriptions", "#b91c1c")],
            "Health": [("Healthcare", "#10b981"), ("Fitness", "#059669")],
            "Finance": [("Transfers", "#6b7280"), ("Payments", "#4b5563"), ("Cash & ATM", "#374151")],
            "Travel": [("Hotels", "#06b6d4"), ("Flights", "#0891b2")],
            "Income": [("Income", "#22c55e"), ("Refunds & Rewards", "#16a34a")],
        }
        sub_map: dict[str, int] = {}
        for parent_name, subs in sub_categories.items():
            for sub_name, color in subs:
                cat = await create(
                    session,
                    CategoryCreate(name=sub_name, color=color, parent_id=parent_map[parent_name]),
                    is_user_defined=False,
                )
                sub_map[sub_name] = cat.id  # type: ignore[assignment]

        # Create rules pointing to sub-categories
        for pattern, is_regex, cat_name, priority in DEFAULT_RULES:
            cat_id = sub_map.get(cat_name) or parent_map.get(cat_name)
            if cat_id:
                await create_rule(session, CategoryRuleCreate(
                    category_id=cat_id,
                    pattern=pattern,
                    is_regex=is_regex,
                    priority=priority,
                ))
        break
