"""Recipe + Ingredient + Plan + Grocery API-Routen (Postgres-persistent)."""
from datetime import date
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict
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
from app.services.grocery_engine import (
    _clean_item_notes,
    build_export_csv,
    build_export_rows,
    build_export_txt,
    generate_and_persist_grocery_list,
    grocery_item_display_name,
    iso_year_by_week,
    sort_by_gang,
)
from app.repositories.household import HouseholdRepository
from app.repositories.member import MemberRepository
from app.core.ownership import (
    get_user_households, require_household, require_household_id,
    require_plan_owner, require_weekly_plan_owner, require_grocery_owner,
)

# Kein router-level dependency: sync-Dep vor async DB-Writes verursacht MissingGreenlet.
# Jede Route deklariert get_current_user_id selbst.
router = APIRouter(tags=["family"])

_MONTH_NAMES_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}


def _plan_stats(plan) -> tuple[str, int, int]:
    """Liefert (deutscher Monatsname, Wochenanzahl, distinct Rezeptanzahl)."""
    weeks = plan.weekly_plans or []
    recipe_ids = {
        slot.recipe_id
        for week in weeks
        for slot in (week.meal_slots or [])
    }
    return _MONTH_NAMES_DE.get(plan.month, ""), len(weeks), len(recipe_ids)


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
        instructions=body.instructions,
        kid_friendly_tip=body.kid_friendly_tip,
        cook_once_eat_twice=body.cook_once_eat_twice,
        tags=body.tags or [],
    )
    return RecipeOut(
        id=recipe.id, title=recipe.title,
        description=recipe.description,
        image_url=recipe.image_url,
        servings=recipe.servings,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        difficulty=recipe.difficulty,
        instructions=recipe.instructions,
        kid_friendly_tip=recipe.kid_friendly_tip,
        cook_once_eat_twice=recipe.cook_once_eat_twice,
        tags=recipe.tags or [],
        created_at=recipe.created_at,
    )


@router.get("/recipes", response_model=list[RecipeOut])
async def list_recipes(
    planned_only: bool = False,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    max_time: Optional[int] = None,
    tag: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet Rezepte, optional gefiltert (Suche, Schwierigkeit, Zeit, Tag).

    planned_only=True: nur Rezepte, die in MealSlots der Pläne des Users vorkommen.
    """
    repo = RecipeRepository(db)
    household_ids = [h.id for h in await get_user_households(db, user_id)]
    recipes = await repo.list_filtered(
        household_ids=household_ids,
        planned_only=planned_only,
        search=search,
        difficulty=difficulty,
        max_time=max_time,
        tag=tag,
    )
    return [
        RecipeOut(
            id=r.id, title=r.title,
            description=r.description,
            image_url=r.image_url,
            servings=r.servings,
            prep_time_minutes=r.prep_time_minutes,
            cook_time_minutes=r.cook_time_minutes,
            difficulty=r.difficulty,
            instructions=r.instructions,
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
    multiplier: float = Query(1.0, ge=0.1, le=20),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = RecipeRepository(db)
    recipe = await repo.get_with_ingredients(rid)
    if not recipe:
        raise HTTPException(status_code=404)
    scaled_servings = round(recipe.servings * multiplier, 1)
    return RecipeOut(
        id=recipe.id, title=recipe.title,
        description=recipe.description,
        image_url=recipe.image_url,
        servings=scaled_servings,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        difficulty=recipe.difficulty,
        instructions=recipe.instructions,
        kid_friendly_tip=recipe.kid_friendly_tip,
        cook_once_eat_twice=recipe.cook_once_eat_twice,
        tags=recipe.tags or [],
        ingredients=[
            {
                "id": ri.id,
                "ingredient_id": ri.ingredient_id,
                "ingredient_name": ri.ingredient.name if ri.ingredient else None,
                "name": ri.ingredient.name if ri.ingredient else None,
                "category": ri.ingredient.category if ri.ingredient else None,
                "quantity": round(ri.quantity * multiplier, 2) if ri.quantity else ri.quantity,
                "unit": ri.unit,
                "is_optional": ri.is_optional,
                "substitution_note": ri.substitution_note,
            }
            for ri in (recipe.ingredients or [])
        ],
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
    # ── Household des Users ermitteln (NICHT user_id als household_id annehmen) ──
    household_repo = HouseholdRepository(db)
    households = await household_repo.get_by_owner(user_id)
    if not households:
        raise HTTPException(
            status_code=404,
            detail="Kein Haushalt für diesen User gefunden – bitte zuerst einen Haushalt anlegen.",
        )
    household = households[0]
    household_id = household.id

    member_repo = MemberRepository(db)
    members = await member_repo.get_by_household(household_id)

    # ── Art. 9 DSGVO: Einwilligung vor Verarbeitung von Gesundheitsdaten pruefen ──
    # Allergien (Haushalt oder Mitglieder) sind Gesundheitsdaten. Ohne dokumentierte
    # Einwilligung darf kein Plan generiert werden, der sie verarbeitet.
    profile_allergies = (household.dietary_profile or {}).get("allergies") or []
    member_allergies = [a for m in members if m.is_active for a in (m.allergies or [])]
    has_health_data = bool(profile_allergies or member_allergies)
    if has_health_data and household.health_data_consent_at is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "Fuer die Verarbeitung von Allergie-Angaben (Gesundheitsdaten nach "
                "Art. 9 DSGVO) fehlt die ausdrueckliche Einwilligung. Bitte im Profil "
                "erteilen, dann Plan erneut generieren."
            ),
        )

    # ── Task 21: Portions-Faktor berechnen ──
    member_dicts = [
        {
            "age": m.age,
            "allergies": m.allergies or [],
            "dietary_goals": m.dietary_goals or {},
        }
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
    # Flag vor commit lesen: expire_on_commit entfernt Custom-Attribute.
    was_created = bool(getattr(monthly, "was_created", True))

    # Einkaufslisten werden vom Generator bereits fuer ALLE Wochen angelegt
    # (mit ISO-Kalenderwoche). Hier nur noch die erste Liste referenzieren,
    # keine zweite Liste erzeugen.
    grocery_list_id = None
    grocery_items_count = 0
    plan_repo = MonthlyPlanRepository(db)
    monthly_full = await plan_repo.get_with_weekly(monthly.id)
    gl_repo = GroceryListRepository(db)
    grocery_lists = await gl_repo.get_by_plan(monthly.id)
    if grocery_lists:
        first_grocery = sorted(
            grocery_lists,
            key=lambda g: (g.week_number is None, g.week_number or 0),
        )[0]
        grocery_list_id = str(first_grocery.id)
        # Explizit laden statt Lazy-Load auf grocery.items (MissingGreenlet vermeiden)
        gi_repo_count = GroceryItemRepository(db)
        grocery_items_count = len(await gi_repo_count.get_by_list(first_grocery.id))

    await db.commit()

    # Weekly-Pläne mit Slots laden für die Response
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
        "created": was_created,
        "updated": not was_created,
        "weeks": len(weeks_data),
        "meal_slots_total": total_slots,
        "total_portions": monthly.total_portions,
        "grocery_list": grocery_list_id,
        "grocery_items": grocery_items_count,
        "weekly_plans": weeks_data,
    }


@router.get("/plans", response_model=list[MonthlyPlanOut])
async def list_plans(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet alle Monatspläne des Users."""
    households = await get_user_households(db, user_id)
    hh_ids = [h.id for h in households]
    if not hh_ids:
        return []
    repo = MonthlyPlanRepository(db)
    plans = await repo.get_all(
        repo.model_class.household_id.in_(hh_ids),
        order_by=repo.model_class.year.desc(),
    )
    result = []
    for p in plans:
        # Relationships explizit laden – Lazy-Load wäre nach commit/async problematisch.
        full = await repo.get_with_weekly(p.id)
        if full is not None:
            month_name, weeks_count, recipe_count = _plan_stats(full)
        else:
            month_name = _MONTH_NAMES_DE.get(p.month, "")
            weeks_count = recipe_count = 0
        result.append(MonthlyPlanOut(
            id=p.id,
            household_id=p.household_id,
            month=p.month,
            year=p.year,
            month_name=month_name,
            weeks_count=weeks_count,
            recipe_count=recipe_count,
            status=p.status,
            focus_tags=p.focus_tags or [],
            generated_at=p.generated_at,
            notes=p.notes,
            total_portions=p.total_portions,
        ))
    return result


@router.get("/plans/{plan_id}", response_model=MonthlyPlanOut)
async def get_plan(
    plan_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Gibt einen Monatsplan zurück."""
    repo = MonthlyPlanRepository(db)
    plan = await repo.get_with_weekly(plan_id)
    plan = await require_plan_owner(db, user_id, plan)  # IDOR-Schutz
    month_name, weeks_count, recipe_count = _plan_stats(plan)
    return MonthlyPlanOut(
        id=plan.id,
        household_id=plan.household_id,
        month=plan.month,
        year=plan.year,
        month_name=month_name,
        weeks_count=weeks_count,
        recipe_count=recipe_count,
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
    weekly = await require_weekly_plan_owner(db, user_id, weekly)  # IDOR-Schutz
    return WeeklyPlanOut(
        id=weekly.id,
        week_number=weekly.week_number,
        start_date=weekly.start_date,
        cw=weekly.start_date.isocalendar()[1] if weekly.start_date else None,
        notes=weekly.notes,
        meal_slots=[
            MealSlotOut(
                id=slot.id,
                day_of_week=slot.day_of_week,
                meal_type=slot.meal_type,
                recipe_id=slot.recipe_id,
                recipe_title=slot.recipe.title if slot.recipe else None,
                recipe_servings=slot.recipe.servings if slot.recipe else None,
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
    plan_repo = MonthlyPlanRepository(db)
    plan = await plan_repo.get(plan_id)
    await require_plan_owner(db, user_id, plan)  # IDOR-Schutz
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
            cw=wp.start_date.isocalendar()[1] if wp.start_date else None,
            notes=wp.notes,
            meal_slots=[
                MealSlotOut(
                    id=s.id, day_of_week=s.day_of_week,
                    meal_type=s.meal_type, recipe_id=s.recipe_id,
                    recipe_title=s.recipe.title if s.recipe else None,
                    recipe_servings=s.recipe.servings if s.recipe else None,
                    servings_multiplier=s.servings_multiplier,
                    is_repeat=s.is_repeat,
                )
                for s in (wp_full.meal_slots if wp_full else [])
            ],
        ))
    return result


# ─── Grocery-Liste generieren ─────────────────────────────────────────────

class GroceryGenerateRequest(BaseModel):
    """Optionaler Body für POST /grocery/generate.

    Ohne Body wird wie bisher der neueste Monatsplan des Haushalts genommen.
    Mit `plan_id` (oder Alias `monthly_plan_id`) wird gezielt dieser Plan
    befüllt. Unbekannte Felder werden mit 422 abgelehnt, damit ein falsch
    benannter Parameter nicht wieder still ins Leere läuft.
    """

    model_config = ConfigDict(extra="forbid")

    plan_id: Optional[UUID] = None
    monthly_plan_id: Optional[UUID] = None


@router.post("/grocery-lists/generate", status_code=201)
@router.post("/grocery/generate", status_code=201, include_in_schema=False)
async def generate_grocery(
    body: Optional[GroceryGenerateRequest] = Body(default=None),
    weekly_plan_id: Optional[UUID] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generiert eine Einkaufsliste aus einem WeeklyPlan.

    Quellen in dieser Reihenfolge:
    1. `weekly_plan_id` (Query) — gezielte Woche
    2. `plan_id` / `monthly_plan_id` (Body) — gezielter Monatsplan
    3. keiner von beiden — neuester Monatsplan des Haushalts
    """
    week_repo = WeeklyPlanRepository(db)
    plan_repo = MonthlyPlanRepository(db)
    recipe_repo = RecipeRepository(db)
    household_id = await require_household_id(db, user_id)  # echter Haushalt, nicht user_id

    if weekly_plan_id:
        weekly = await week_repo.get_with_slots(weekly_plan_id)
        weekly = await require_weekly_plan_owner(db, user_id, weekly)  # IDOR-Schutz
        grocery = await generate_and_persist_grocery_list(
            weekly, db,
            household_id=household_id,
            monthly_plan_id=weekly.monthly_plan_id,
            week_number=(
                weekly.start_date.isocalendar()[1]
                if weekly.start_date else None
            ),
        )
    else:
        requested_plan_id = None
        if body is not None:
            requested_plan_id = body.plan_id or body.monthly_plan_id

        if requested_plan_id:
            # Gezielt angeforderter Plan — nie still auf einen anderen ausweichen.
            latest = await plan_repo.get(requested_plan_id)
            latest = await require_plan_owner(db, user_id, latest)
        else:
            # Letzten Monatsplan des Haushalts verwenden
            latest = await plan_repo.get_latest_for_household(household_id)
        if not latest:
            raise HTTPException(status_code=400, detail="No plans found – generate a plan first")

        weekly_plans = await week_repo.get_all(
            week_repo.model_class.monthly_plan_id == latest.id,
            order_by=week_repo.model_class.week_number,
        )
        if not weekly_plans:
            raise HTTPException(status_code=400, detail="No weekly plans found")

        # Einkaufsfrequenz aus dem Haushaltsprofil lesen.
        household_repo = HouseholdRepository(db)
        household = await household_repo.get(household_id)
        shopping_frequency = (
            (household.dietary_profile or {}).get("shopping_frequency")
            if household else None
        )
        is_master = shopping_frequency in (None, "", "nach_bedarf")

        if is_master:
            # Master-Liste: alle Slots des Monats in einer Einkaufsliste zusammenfassen.
            from types import SimpleNamespace
            from typing import cast
            from app.models.database import WeeklyPlan as _WeeklyPlan

            all_slots = []
            for wp in weekly_plans:
                wp_full = await week_repo.get_with_slots(wp.id)
                if wp_full and wp_full.meal_slots:
                    all_slots.extend(wp_full.meal_slots)

            dummy_plan = cast(_WeeklyPlan, SimpleNamespace(meal_slots=all_slots))
            grocery = await generate_and_persist_grocery_list(
                dummy_plan, db,
                household_id=household_id,
                monthly_plan_id=latest.id,
                week_number=None,
            )
        else:
            weekly = await week_repo.get_with_slots(weekly_plans[0].id)
            if weekly is None:
                raise HTTPException(status_code=404, detail="Weekly plan not found")
            grocery = await generate_and_persist_grocery_list(
                weekly, db,
                household_id=household_id,
                monthly_plan_id=latest.id,
                week_number=(
                    weekly.start_date.isocalendar()[1]
                    if weekly.start_date else None
                ),
            )

    await db.commit()

    gi_repo = GroceryItemRepository(db)
    items = await gi_repo.get_by_list(grocery.id)

    # Supermarkt aus dem Haushaltsprofil für die Gang-Sortierung lesen.
    household_repo = HouseholdRepository(db)
    household = await household_repo.get(household_id)
    supermarket = (
        (household.dietary_profile or {}).get("preferred_supermarket", "Rewe")
        if household else "Rewe"
    )

    rows = [
        {
            "id": str(item.id),
            "ingredient_id": str(item.ingredient_id),
            "quantity_total": item.quantity_total,
            "unit": item.unit,
            "category": item.category_override or "other",
            "is_checked": item.is_checked,
            "notes": _clean_item_notes(item.notes),
            "name": grocery_item_display_name(
                item.ingredient.name if item.ingredient else "Zutat",
                item.notes,
                item.category_override or "other",
            ),
        }
        for item in items
    ]
    return {
        "grocery_list_id": str(grocery.id),
        "monthly_plan_id": str(grocery.monthly_plan_id) if grocery.monthly_plan_id else None,
        "week_number": grocery.week_number,
        "is_master_list": grocery.is_master_list,
        "segment_label": getattr(grocery, "segment_label", None),
        "items": sort_by_gang(rows, supermarket=supermarket),
    }


@router.get("/grocery-lists/{gl_id}/export")
async def export_grocery_list(
    gl_id: UUID,
    fmt: str = Query("csv", alias="format", pattern="^(csv|txt)$"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Exportiert eine Einkaufsliste als CSV oder TXT.

    CSV: Semikolon-getrennt, UTF-8 mit BOM, CRLF – öffnet in deutschem Excel
    ohne Import-Dialog. Spalten: Menge; Einheit; Zutat; Gang.
    TXT: druckbare Liste mit Gang-Überschriften.
    Nur eigene Haushalte (IDOR-Schutz); fremde/nicht existierende Listen → 404.
    """
    repo = GroceryListRepository(db)
    gl = await repo.get_with_items(gl_id)
    gl = await require_grocery_owner(db, user_id, gl)  # IDOR-Schutz, 404

    # Supermarkt-Label für den TXT-Kopf (optional, Fallback "Rewe")
    supermarket = "Rewe"
    try:
        households = await get_user_households(db, user_id)
        for h in households:
            if h.id == gl.household_id:
                supermarket = (h.dietary_profile or {}).get("preferred_supermarket", "Rewe")
                break
    except Exception:
        pass  # Export darf nicht an optionalem Label scheitern

    # Items über das Repository laden: eager-load von ingredient, sonst
    # MissingGreenlet beim Zugriff auf item.ingredient in async-Session.
    gi_repo = GroceryItemRepository(db)
    raw_items = await gi_repo.get_by_list(gl.id)
    # Task 82: Gang-Reihenfolge richtet sich nach dem Supermarkt-Profil.
    rows = build_export_rows(raw_items, supermarket=supermarket)
    suffix = f"kw{gl.week_number}" if gl.week_number is not None else "monat"
    filename = f"einkaufsliste_{suffix}_{str(gl.id)[:8]}.{fmt}"

    if fmt == "csv":
        payload = "\ufeff" + build_export_csv(rows, supermarket=supermarket)
        media_type = "text/csv; charset=utf-8"
    else:
        payload = build_export_txt(rows, week_number=gl.week_number, supermarket=supermarket)
        media_type = "text/plain; charset=utf-8"

    return Response(
        content=payload.encode("utf-8"),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/grocery-lists", response_model=list[GroceryListOut])
async def list_grocery_lists(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Listet Einkaufslisten aller Haushalte des Users."""
    households = await get_user_households(db, user_id)
    hh_ids = [h.id for h in households]
    if not hh_ids:
        return []

    repo = GroceryListRepository(db)
    lists = await repo.get_all(
        repo.model_class.household_id.in_(hh_ids),
        order_by=repo.model_class.generated_at.desc(),
    )

    # Supermarkt aus dietary_profile lesen
    supermarket = "Rewe"
    if households:
        dp = households[0].dietary_profile or {}
        supermarket = dp.get("preferred_supermarket", "Rewe")

    gi_repo_list = GroceryItemRepository(db)
    # Task 75: ISO-Jahr je (Plan, KW) einmalig auflösen – kein N+1 und keine
    # geratene Jahresangabe, wenn ein Plan kein Wochen-Startdatum hat.
    iso_years = await iso_year_by_week(db, [gl.monthly_plan_id for gl in lists])
    result = []
    for gl in lists:
        # Explizit laden statt Lazy-Load auf gl.items (MissingGreenlet vermeiden)
        raw_items = await gi_repo_list.get_by_list(gl.id)
        items = sort_by_gang(
            [
                GroceryItemOut(
                    id=item.id,
                    ingredient_name=grocery_item_display_name(
                        item.ingredient.name if item.ingredient else str(item.ingredient_id),
                        item.notes,
                        item.category_override or "other",
                    ),
                    category=item.category_override or "other",
                    quantity_total=item.quantity_total,
                    unit=item.unit,
                    is_checked=item.is_checked,
                    notes=_clean_item_notes(item.notes),
                )
                for item in raw_items
            ],
            name_key="ingredient_name",
            supermarket=supermarket,
        )
        # Task 85: segment_label ist kein DB-Feld. Wir leiten es aus der
        # Position ab, wenn mehrere Listen dieselbe KW teilen (Einkaufstage).
        # Task 75: Segmentierung gilt nur innerhalb desselben Plans – KW 1 aus
        # 2026 und KW 1 aus 2027 sind verschiedene Wochen, nicht zwei Segmente.
        _label = getattr(gl, "segment_label", None)
        if _label is None and not gl.is_master_list and gl.week_number is not None:
            _same_week = [
                g for g in lists
                if g.week_number == gl.week_number
                and g.monthly_plan_id == gl.monthly_plan_id
                and not g.is_master_list
            ]
            if len(_same_week) > 1:
                _idx = next((i for i, g in enumerate(_same_week) if g.id == gl.id), 0) + 1
                _label = f"Einkauf {_idx}/{len(_same_week)}"
        result.append(GroceryListOut(
            id=gl.id,
            week_number=gl.week_number,
            cw=gl.week_number,
            iso_year=(
                iso_years.get((gl.monthly_plan_id, gl.week_number))
                if gl.week_number is not None
                else None
            ),
            is_master_list=gl.is_master_list,
            generated_at=gl.generated_at,
            supermarket=supermarket,
            segment_label=_label,
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
    gl = await require_grocery_owner(db, user_id, gl)  # IDOR-Schutz
    gi_repo = GroceryItemRepository(db)
    raw_items = await gi_repo.get_by_list(gl.id)

    # Supermarkt aus dem Haushaltsprofil lesen (Fallback "Rewe").
    supermarket = "Rewe"
    try:
        households = await get_user_households(db, user_id)
        for h in households:
            if h.id == gl.household_id:
                supermarket = (h.dietary_profile or {}).get("preferred_supermarket", "Rewe")
                break
    except Exception:
        pass

    items = []
    if raw_items:
        items = sort_by_gang(
            [
                GroceryItemOut(
                    id=item.id,
                    ingredient_name=grocery_item_display_name(
                        item.ingredient.name if item.ingredient else str(item.ingredient_id),
                        item.notes,
                        item.category_override or "other",
                    ),
                    category=item.category_override or "other",
                    quantity_total=item.quantity_total,
                    unit=item.unit,
                    is_checked=item.is_checked,
                    notes=_clean_item_notes(item.notes),
                )
                for item in raw_items
            ],
            name_key="ingredient_name",
            supermarket=supermarket,
        )
    # Task 75: ISO-Jahr zur gespeicherten KW aus dem Wochen-Startdatum.
    iso_years = await iso_year_by_week(db, [gl.monthly_plan_id])

    return GroceryListOut(
        id=gl.id,
        week_number=gl.week_number,
        cw=gl.week_number,
        iso_year=(
            iso_years.get((gl.monthly_plan_id, gl.week_number))
            if gl.week_number is not None
            else None
        ),
        is_master_list=gl.is_master_list,
        generated_at=gl.generated_at,
        supermarket=supermarket,
        segment_label=getattr(gl, "segment_label", None),
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