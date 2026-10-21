"""Recipe + Ingredient + Plan + Grocery API-Routen (In-Memory)"""
from datetime import datetime, date, UTC
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user_id
from app.schemas.api import (
    RecipeCreate, RecipeOut, IngredientCreate, IngredientOut,
    MonthlyPlanCreate, MonthlyPlanOut,
    GroceryListOut, GroceryItemOut,
)
from app.services.plan_generator import GeneratorConfig, generate_monthly_plan
from app.services.grocery_engine import build_grocery_list

router = APIRouter(tags=["family"], dependencies=[Depends(get_current_user_id)])

# In-Memory
_RECIPES: dict[str, dict] = {}
_INGREDIENTS: dict[str, dict] = {}
_PLANS: dict[str, dict] = {}
_GROCERY_LISTS: dict[str, dict] = {}


# ─── Ingredients ──────────────────────────────────────────────────────────

@router.post("/ingredients", response_model=IngredientOut, status_code=201)
async def create_ingredient(body: IngredientCreate, user_id: str = Depends(get_current_user_id)):
    iid = str(uuid4())
    _INGREDIENTS[iid] = {"id": iid, "name": body.name, "category": body.category, "unit_default": body.unit_default, "storage": body.storage}
    return IngredientOut(id=UUID(iid), name=body.name, category=body.category, unit_default=body.unit_default, storage=body.storage)


@router.get("/ingredients", response_model=list[IngredientOut])
async def list_ingredients(user_id: str = Depends(get_current_user_id)):
    return [IngredientOut(id=UUID(i["id"]), name=i["name"], category=i["category"], unit_default=i["unit_default"], storage=i["storage"]) for i in _INGREDIENTS.values()]


# ─── Recipes ──────────────────────────────────────────────────────────────

@router.post("/recipes", response_model=RecipeOut, status_code=201)
async def create_recipe(body: RecipeCreate, user_id: str = Depends(get_current_user_id)):
    rid = str(uuid4())
    _RECIPES[rid] = {
        "id": rid, "household_id": user_id,
        "title": body.title, "description": body.description,
        "servings": body.servings, "prep_time_minutes": body.prep_time_minutes,
        "cook_time_minutes": body.cook_time_minutes, "difficulty": body.difficulty,
        "kid_friendly_tip": body.kid_friendly_tip,
        "cook_once_eat_twice": body.cook_once_eat_twice,
        "tags": body.tags or [],
        "created_at": datetime.now(UTC),
    }
    return RecipeOut(
        id=UUID(rid), title=body.title, description=body.description,
        servings=body.servings, prep_time_minutes=body.prep_time_minutes,
        cook_time_minutes=body.cook_time_minutes, difficulty=body.difficulty,
        kid_friendly_tip=body.kid_friendly_tip,
        cook_once_eat_twice=body.cook_once_eat_twice,
        tags=body.tags or [], created_at=_RECIPES[rid]["created_at"],
    )


@router.get("/recipes", response_model=list[RecipeOut])
async def list_recipes(user_id: str = Depends(get_current_user_id)):
    return [RecipeOut(id=UUID(r["id"]), title=r["title"], description=r["description"], servings=r["servings"], prep_time_minutes=r["prep_time_minutes"], cook_time_minutes=r["cook_time_minutes"], difficulty=r["difficulty"], kid_friendly_tip=r["kid_friendly_tip"], cook_once_eat_twice=r["cook_once_eat_twice"], tags=r["tags"] or [], created_at=r["created_at"]) for r in _RECIPES.values()]


@router.get("/recipes/{rid}", response_model=RecipeOut)
async def get_recipe(rid: str, user_id: str = Depends(get_current_user_id)):
    r = _RECIPES.get(rid)
    if not r:
        raise HTTPException(status_code=404)
    return RecipeOut(id=UUID(rid), title=r["title"], description=r["description"], servings=r["servings"], prep_time_minutes=r["prep_time_minutes"], cook_time_minutes=r["cook_time_minutes"], difficulty=r["difficulty"], kid_friendly_tip=r["kid_friendly_tip"], cook_once_eat_twice=r["cook_once_eat_twice"], tags=r["tags"] or [], created_at=r["created_at"])


# ─── Plan-Generierung ────────────────────────────────────────────────────

@router.post("/plans/generate", status_code=201)
async def generate_plan(body: MonthlyPlanCreate, user_id: str = Depends(get_current_user_id)):
    """Generiert einen Monatsplan basierend auf konfigurierten Rezepten + Mitgliedern."""
    recipe_ids = [UUID(rid) for rid in _RECIPES.keys()]
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
    pid = str(uuid4())
    _PLANS[pid] = {"id": pid, "household_id": user_id, "month": body.month, "year": body.year, "status": "draft", "focus_tags": body.focus_tags, "generated_at": datetime.now(UTC)}
    return {"plan_id": pid, "month": body.month, "year": body.year, "weeks": len(plan["weeks"]), "meal_slots_total": sum(len(w["meal_slots"]) for w in plan["weeks"])}


# ─── Grocery-Liste generieren ─────────────────────────────────────────────

@router.post("/grocery/generate", status_code=201)
async def generate_grocery(user_id: str = Depends(get_current_user_id)):
    """Generiert eine Einkaufsliste aus dem aktuellen Plan (vereinfacht)."""
    if not _RECIPES:
        raise HTTPException(status_code=400, detail="No recipes found")

    # Dummy-Ingredients-Lookup aus dem Store
    ingredients_lookup = {UUID(k): {"name": v["name"], "category": v["category"]} for k, v in _INGREDIENTS.items()}

    # Vereinfachter Wochenplan aus allen Rezepten
    from app.services.grocery_engine import register_dummy_recipe
    for rid, r in _RECIPES.items():
        # Jedes Rezept bekommt eine Dummy-Zutat (wenn keine vorhanden)
        pass

    # Für den Test: Erzeuge einen Dummy-Plan aus allen Rezepten je einmal
    # (in der echten Version kommt der Plan aus der DB)
    dummy_plan = {
        "meal_slots": [
            {"recipe_id": UUID(rid), "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False}
            for rid in _RECIPES.keys()
        ]
    }
    result = build_grocery_list(dummy_plan, ingredients_lookup)

    glid = str(uuid4())
    _GROCERY_LISTS[glid] = {"id": glid, "items": result["items"]}
    return {"grocery_list_id": glid, "items": result["items"], "grouped": result["grouped"]}


# ─── Stripe-Scaffold ──────────────────────────────────────────────────────

@router.post("/stripe/create-checkout-session")
async def create_checkout_session(user_id: str = Depends(get_current_user_id)):
    """Erzeugt einen Stripe-Checkout-Session-Stub (Testmodus).

    In Produktion: stripe.checkout.Session.create(...)
    """
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
    """Stripe-Webhook-Stub (noch ohne Verarbeitung).
    
    In Produktion: Event-Verifikation + subscription-activation.
    """
    return {"status": "received", "handled": False, "note": "Webhook-Handler noch nicht implementiert."}