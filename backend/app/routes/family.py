"""Recipe + Ingredient + Plan + Grocery API-Routen (Postgres-persistent)."""
from datetime import datetime, date, UTC
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.api import (
    RecipeCreate, RecipeOut, IngredientCreate, IngredientOut,
    MonthlyPlanCreate, MonthlyPlanOut,
    GroceryListOut, GroceryItemOut,
)
from app.repositories.ingredient import IngredientRepository
from app.repositories.recipe import RecipeRepository
from app.repositories.plan import MonthlyPlanRepository
from app.repositories.grocery import GroceryListRepository
from app.services.plan_generator import GeneratorConfig, generate_monthly_plan
from app.services.grocery_engine import build_grocery_list

router = APIRouter(tags=["family"], dependencies=[Depends(get_current_user_id)])


# ─── Ingredients ──────────────────────────────────────────────────────────

@router.post("/ingredients", response_model=IngredientOut, status_code=201)
async def create_ingredient(
    body: IngredientCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = IngredientRepository(db)
    ingredient = await repo.create(
        name=body.name,
        category=body.category,
        unit_default=body.unit_default,
        storage=body.storage,
    )
    return IngredientOut(
        id=ingredient.id,
        name=ingredient.name,
        category=ingredient.category,
        unit_default=ingredient.unit_default,
        storage=ingredient.storage,
    )


@router.get("/ingredients", response_model=list[IngredientOut])
async def list_ingredients(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = IngredientRepository(db)
    ingredients = await repo.get_all(order_by=repo.model_class.name)
    return [
        IngredientOut(
            id=i.id, name=i.name, category=i.category,
            unit_default=i.unit_default, storage=i.storage,
        )
        for i in ingredients
    ]


# ─── Recipes ──────────────────────────────────────────────────────────────

@router.post("/recipes", response_model=RecipeOut, status_code=201)
async def create_recipe(
    body: RecipeCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = RecipeRepository(db)
    recipe = await repo.create(
        household_id=UUID(user_id),
        title=body.title,
        description=body.description,
        servings=body.servings,
        prep_time_minutes=body.prep_time_minutes,
        cook_time_minutes=body.cook_time_minutes,
        difficulty=body.difficulty,
        kid_friendly_tip=body.kid_friendly_tip,
        cook_once_eat_twice=body.cook_once_eat_twice,
        tags=body.tags or [],
    )
    return RecipeOut(
        id=recipe.id, title=recipe.title,
        description=recipe.description,
        servings=recipe.servings,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        difficulty=recipe.difficulty,
        kid_friendly_tip=recipe.kid_friendly_tip,
        cook_once_eat_twice=recipe.cook_once_eat_twice,
        tags=recipe.tags or [],
        created_at=recipe.created_at,
    )


@router.get("/recipes", response_model=list[RecipeOut])
async def list_recipes(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = RecipeRepository(db)
    recipes = await repo.get_all()
    return [
        RecipeOut(
            id=r.id, title=r.title,
            description=r.description,
            servings=r.servings,
            prep_time_minutes=r.prep_time_minutes,
            cook_time_minutes=r.cook_time_minutes,
            difficulty=r.difficulty,
            kid_friendly_tip=r.kid_friendly_tip,
            cook_once_eat_twice=r.cook_once_eat_twice,
            tags=r.tags or [],
            created_at=r.created_at,
        )
        for r in recipes
    ]


@router.get("/recipes/{rid}", response_model=RecipeOut)
async def get_recipe(
    rid: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = RecipeRepository(db)
    recipe = await repo.get(rid)
    if not recipe:
        raise HTTPException(status_code=404)
    return RecipeOut(
        id=recipe.id, title=recipe.title,
        description=recipe.description,
        servings=recipe.servings,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        difficulty=recipe.difficulty,
        kid_friendly_tip=recipe.kid_friendly_tip,
        cook_once_eat_twice=recipe.cook_once_eat_twice,
        tags=recipe.tags or [],
        created_at=recipe.created_at,
    )


# ─── Plan-Generierung ────────────────────────────────────────────────────

@router.post("/plans/generate", status_code=201)
async def generate_plan(
    body: MonthlyPlanCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generiert einen Monatsplan basierend auf vorhandenen Rezepten."""
    recipe_repo = RecipeRepository(db)
    all_recipes = await recipe_repo.get_all()
    recipe_ids = [r.id for r in all_recipes]
    if not recipe_ids:
        raise HTTPException(status_code=400, detail="No recipes found – create recipes first")

    config = GeneratorConfig(
        household_id=UUID(user_id),
        month=body.month,
        year=body.year,
        member_ids=[],
        recipe_ids=recipe_ids,
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        focus_tags=body.focus_tags,
    )
    plan = generate_monthly_plan(config)

    # Monatsplan in DB persistieren
    plan_repo = MonthlyPlanRepository(db)
    monthly = await plan_repo.create(
        household_id=UUID(user_id),
        month=body.month,
        year=body.year,
        status="draft",
        focus_tags=body.focus_tags or [],
        generated_at=datetime.now(UTC),
    )

    return {
        "plan_id": str(monthly.id),
        "month": body.month,
        "year": body.year,
        "weeks": len(plan["weeks"]),
        "meal_slots_total": sum(len(w["meal_slots"]) for w in plan["weeks"]),
    }


# ─── Grocery-Liste generieren ─────────────────────────────────────────────

@router.post("/grocery/generate", status_code=201)
async def generate_grocery(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generiert eine Einkaufsliste aus dem aktuellen Plan."""
    recipe_repo = RecipeRepository(db)
    all_recipes = await recipe_repo.get_all()
    if not all_recipes:
        raise HTTPException(status_code=400, detail="No recipes found")

    ings = IngredientRepository(db)
    all_ingredients = await ings.get_all()
    ingredients_lookup = {
        i.id: {"name": i.name, "category": i.category}
        for i in all_ingredients
    }

    dummy_plan = {
        "meal_slots": [
            {"recipe_id": r.id, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False}
            for r in all_recipes
        ]
    }
    result = build_grocery_list(dummy_plan, ingredients_lookup)

    # Einkaufsliste in DB speichern
    gl_repo = GroceryListRepository(db)
    grocery = await gl_repo.create(
        household_id=UUID(user_id),
        monthly_plan_id=None,
        week_number=None,
        is_master_list=True,
    )

    return {
        "grocery_list_id": str(grocery.id),
        "items": result["items"],
        "grouped": result["grouped"],
    }


# ─── Stripe-Scaffold ──────────────────────────────────────────────────────

@router.post("/stripe/create-checkout-session")
async def create_checkout_session(user_id: str = Depends(get_current_user_id)):
    """Erzeugt einen Stripe-Checkout-Session-Stub (Testmodus)."""
    return {
        "stub": True,
        "message": "Stripe-Testmodus: Keine echte Zahlung ausgelöst.",
        "checkout_url": f"https://checkout.stripe.com/pay/test_session_{user_id[:8]}",
        "price_id": "price_monthly_2999",
        "amount": 2999,
        "currency": "eur",
    }


@router.post("/stripe/webhook")
async def stripe_webhook_stub():
    """Stripe-Webhook-Stub (noch ohne Verarbeitung)."""
    return {"status": "received", "handled": False, "note": "Webhook-Handler noch nicht implementiert."}