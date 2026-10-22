"""Recipe + Ingredient + Plan + Grocery API-Routen (Postgres-persistent)."""
from datetime import date
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.schemas.api import (
    RecipeCreate, RecipeOut, IngredientCreate, IngredientOut,
    MonthlyPlanCreate, MonthlyPlanOut,
    GroceryListOut, GroceryItemOut,
    WeeklyPlanOut, MealSlotOut,
)
from app.repositories.ingredient import IngredientRepository
from app.repositories.recipe import RecipeRepository
from app.repositories.plan import MonthlyPlanRepository, WeeklyPlanRepository
from app.repositories.grocery import GroceryListRepository, GroceryItemRepository
from app.services.plan_generator import (
    GeneratorConfig, generate_and_persist_monthly_plan, weeks_in_month,
    calculate_total_portions,
)
from app.services.grocery_engine import generate_and_persist_grocery_list
from app.repositories.household import HouseholdRepository
from app.repositories.member import MemberRepository

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
    """Generiert einen Monatsplan basierend auf vorhandenen Rezepten und persistiert ihn.

    Sprint D – Tasks 16–21:
    - Lädt dietary_profile aus Household (Task 16)
    - Lädt Members + deren Allergien + Alter (Tasks 17, 21)
    - Filtert Rezepte nach Ess-Typ, Allergenen, Abwechslung (Tasks 16, 17, 19)
    - Wendet Balanceregel pro Woche an (Task 20)
    - Speichert total_portions im MonthlyPlan (Task 21)
    """
    household_id = UUID(user_id)

    # ── Household + Members laden ──
    household_repo = HouseholdRepository(db)
    household = await household_repo.get(household_id)

    member_repo = MemberRepository(db)
    members = await member_repo.get_by_household(household_id)

    # ── Task 21: Portions-Faktor berechnen ──
    member_dicts = [
        {"age": m.age, "allergies": m.allergies or []}
        for m in members if m.is_active
    ]
    total_portions = calculate_total_portions(member_dicts)

    # ── Alle Rezept-IDs laden ──
    recipe_repo = RecipeRepository(db)
    all_recipes = await recipe_repo.get_all()
    recipe_ids = [r.id for r in all_recipes]
    if not recipe_ids:
        raise HTTPException(status_code=400, detail="No recipes found – create recipes first")

    config = GeneratorConfig(
        household_id=household_id,
        month=body.month,
        year=body.year,
        member_ids=[m.id for m in members],
        recipe_ids=recipe_ids,
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        focus_tags=body.focus_tags,
        # Sprint D
        dietary_profile=household.dietary_profile if household else {},
        members=member_dicts,
        total_portions=total_portions,
    )

    monthly = await generate_and_persist_monthly_plan(config, db)
    await db.commit()

    # Weekly-Pläne mit Slots laden für die Response
    plan_repo = MonthlyPlanRepository(db)
    monthly_full = await plan_repo.get_with_weekly(monthly.id)

    weeks_data = []
    total_slots = 0
    if monthly_full:
        for wp in monthly_full.weekly_plans:
            slot_count = len(wp.meal_slots) if wp.meal_slots else 0
            total_slots += slot_count
            weeks_data.append({
                "week_number": wp.week_number,
                "start_date": str(wp.start_date) if wp.start_date else None,
                "slots": slot_count,
            })

    return {
        "plan_id": str(monthly.id),
        "month": body.month,
        "year": body.year,
        "weeks": len(weeks_data),
        "meal_slots_total": total_slots,
        "total_portions": monthly.total_portions,
        "weekly_plans": weeks_data,
    }


@router.get("/plans", response_model=list[MonthlyPlanOut])
async def list_plans(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet alle Monatspläne des Users."""
    repo = MonthlyPlanRepository(db)
    plans = await repo.get_all(
        repo.model_class.household_id == UUID(user_id),
        order_by=repo.model_class.year.desc(),
    )
    return [
        MonthlyPlanOut(
            id=p.id,
            household_id=p.household_id,
            month=p.month,
            year=p.year,
            status=p.status,
            focus_tags=p.focus_tags or [],
            generated_at=p.generated_at,
            notes=p.notes,
            total_portions=p.total_portions,
        )
        for p in plans
    ]


@router.get("/plans/{plan_id}", response_model=MonthlyPlanOut)
async def get_plan(
    plan_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Gibt einen Monatsplan zurück."""
    repo = MonthlyPlanRepository(db)
    plan = await repo.get_with_weekly(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return MonthlyPlanOut(
        id=plan.id,
        household_id=plan.household_id,
        month=plan.month,
        year=plan.year,
        status=plan.status,
        focus_tags=plan.focus_tags or [],
        generated_at=plan.generated_at,
        notes=plan.notes,
        total_portions=plan.total_portions,
    )


# ─── Weekly Plan Detail ───────────────────────────────────────────────────

@router.get("/weekly-plans/{wp_id}", response_model=WeeklyPlanOut)
async def get_weekly_plan(
    wp_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Gibt einen Wochenplan mit allen MealSlots zurück."""
    repo = WeeklyPlanRepository(db)
    weekly = await repo.get_with_slots(wp_id)
    if not weekly:
        raise HTTPException(status_code=404, detail="WeeklyPlan not found")
    return WeeklyPlanOut(
        id=weekly.id,
        week_number=weekly.week_number,
        start_date=weekly.start_date,
        notes=weekly.notes,
        meal_slots=[
            MealSlotOut(
                id=slot.id,
                day_of_week=slot.day_of_week,
                meal_type=slot.meal_type,
                recipe_id=slot.recipe_id,
                servings_multiplier=slot.servings_multiplier,
                is_repeat=slot.is_repeat,
            )
            for slot in (weekly.meal_slots or [])
        ],
    )


# ─── Weekly Plans by Month ────────────────────────────────────────────────

@router.get("/plans/{plan_id}/weeks", response_model=list[WeeklyPlanOut])
async def list_weekly_plans(
    plan_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet alle Wochenpläne eines Monatsplans."""
    repo = WeeklyPlanRepository(db)
    weekly_plans = await repo.get_all(
        repo.model_class.monthly_plan_id == plan_id,
        order_by=repo.model_class.week_number,
    )
    result = []
    for wp in weekly_plans:
        # Lade Slots
        wp_full = await repo.get_with_slots(wp.id)
        result.append(WeeklyPlanOut(
            id=wp.id,
            week_number=wp.week_number,
            start_date=wp.start_date,
            notes=wp.notes,
            meal_slots=[
                MealSlotOut(
                    id=s.id, day_of_week=s.day_of_week,
                    meal_type=s.meal_type, recipe_id=s.recipe_id,
                    servings_multiplier=s.servings_multiplier,
                    is_repeat=s.is_repeat,
                )
                for s in (wp_full.meal_slots if wp_full else [])
            ],
        ))
    return result


# ─── Grocery-Liste generieren ─────────────────────────────────────────────

@router.post("/grocery/generate", status_code=201)
async def generate_grocery(
    weekly_plan_id: Optional[UUID] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generiert eine Einkaufsliste aus einem WeeklyPlan."""
    week_repo = WeeklyPlanRepository(db)
    plan_repo = MonthlyPlanRepository(db)
    recipe_repo = RecipeRepository(db)

    if weekly_plan_id:
        weekly = await week_repo.get_with_slots(weekly_plan_id)
        if not weekly:
            raise HTTPException(status_code=404, detail="WeeklyPlan not found")
        grocery = await generate_and_persist_grocery_list(
            weekly, db,
            household_id=UUID(user_id),
            monthly_plan_id=weekly.monthly_plan_id,
            week_number=weekly.week_number,
        )
    else:
        # Letzten Monatsplan verwenden
        latest = await plan_repo.get_latest_for_household(UUID(user_id))
        if not latest:
            raise HTTPException(status_code=400, detail="No plans found – generate a plan first")

        weekly_plans = await week_repo.get_all(
            week_repo.model_class.monthly_plan_id == latest.id,
            order_by=week_repo.model_class.week_number,
        )
        if not weekly_plans:
            raise HTTPException(status_code=400, detail="No weekly plans found")

        weekly = await week_repo.get_with_slots(weekly_plans[0].id)
        grocery = await generate_and_persist_grocery_list(
            weekly, db,
            household_id=UUID(user_id),
            monthly_plan_id=latest.id,
            week_number=weekly.week_number,
        )

    await db.commit()

    gi_repo = GroceryItemRepository(db)
    items = await gi_repo.get_by_list(grocery.id)

    return {
        "grocery_list_id": str(grocery.id),
        "week_number": grocery.week_number,
        "is_master_list": grocery.is_master_list,
        "items": [
            {
                "id": str(item.id),
                "ingredient_id": str(item.ingredient_id),
                "quantity_total": item.quantity_total,
                "unit": item.unit,
                "category": item.category_override or "other",
                "is_checked": item.is_checked,
                "notes": item.notes,
            }
            for item in items
        ],
    }


@router.get("/grocery-lists", response_model=list[GroceryListOut])
async def list_grocery_lists(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet Einkaufslisten eines Households."""
    from app.repositories.household import HouseholdRepository

    repo = GroceryListRepository(db)
    lists = await repo.get_by_household(UUID(user_id))

    # Supermarkt aus dietary_profile lesen
    hh_repo = HouseholdRepository(db)
    households = await hh_repo.get_by_owner(UUID(user_id))
    supermarket = "Rewe"
    if households:
        dp = households[0].dietary_profile or {}
        supermarket = dp.get("preferred_supermarket", "Rewe")

    result = []
    for gl in lists:
        items = []
        if gl.items:
            items = [
                GroceryItemOut(
                    id=item.id,
                    ingredient_name=str(item.ingredient_id),
                    category=item.category_override or "other",
                    quantity_total=item.quantity_total,
                    unit=item.unit,
                    is_checked=item.is_checked,
                    notes=item.notes,
                )
                for item in gl.items
            ]
        result.append(GroceryListOut(
            id=gl.id,
            week_number=gl.week_number,
            is_master_list=gl.is_master_list,
            generated_at=gl.generated_at,
            supermarket=supermarket,
            items=items,
        ))
    return result


@router.get("/grocery-lists/{gl_id}", response_model=GroceryListOut)
async def get_grocery_list(
    gl_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Gibt eine Einkaufsliste mit Items zurück."""
    repo = GroceryListRepository(db)
    gl = await repo.get_with_items(gl_id)
    if not gl:
        raise HTTPException(status_code=404, detail="GroceryList not found")
    items = []
    if gl.items:
        items = [
            GroceryItemOut(
                id=item.id,
                ingredient_name=str(item.ingredient_id),
                category=item.category_override or "other",
                quantity_total=item.quantity_total,
                unit=item.unit,
                is_checked=item.is_checked,
                notes=item.notes,
            )
            for item in gl.items
        ]
    return GroceryListOut(
        id=gl.id,
        week_number=gl.week_number,
        is_master_list=gl.is_master_list,
        generated_at=gl.generated_at,
        items=items,
    )


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