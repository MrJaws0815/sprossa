"""Swap-Service: Rezept in einem MealSlot tauschen.

Task 32 – Rezept-SWAP.

Regeln:
- Owner-Check via ownership.py (IDOR-Schutz).
- Ernährungsprofil (diet_type) + Allergien aller Haushaltsmitglieder
  werden über die bestehende Filterlogik aus plan_generator.py geprüft.
- Niemals dasselbe Rezept zurückgeben, das bereits im Slot ist.
- Bevorzugt Rezepte, die im aktuellen Plan noch nicht vorkommen.
- Kein passendes Rezept → HTTP 409 (kein stiller Fallback).
- Einkaufsliste: Die betroffene Wochen-Einkaufsliste wird gelöscht und
  neu generiert. Das ist die einfachste korrekte Variante, da das
  GroceryList-Modell kein "stale"-Flag besitzt. So wird beim nächsten
  Abruf automatisch eine aktuelle Liste erzeugt (bzw. hier direkt neu
  generiert).
"""
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ownership import require_plan_owner
from app.models.database import (
    GroceryItem,
    GroceryList,
    MealSlot,
    Recipe,
    RecipeIngredient,
    WeeklyPlan,
)
from app.repositories.grocery import GroceryListRepository
from app.repositories.household import HouseholdRepository
from app.repositories.member import MemberRepository
from app.repositories.plan import (
    MealSlotRepository,
    MonthlyPlanRepository,
    WeeklyPlanRepository,
)
from app.services.grocery_engine import (
    generate_and_persist_grocery_list,
    iso_year_week,
)
from app.services.plan_generator import (
    _build_ingredient_index,
    _filter_by_allergens,
    _filter_by_diet,
)


def _slot_payload(slot: MealSlot, recipe: Recipe) -> dict:
    """Baut die API-Response für einen getauschten Slot."""
    return {
        "id": slot.id,
        "recipe": {
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "servings": recipe.servings,
            "prep_time_minutes": recipe.prep_time_minutes,
            "cook_time_minutes": recipe.cook_time_minutes,
            "difficulty": recipe.difficulty,
            "tags": recipe.tags or [],
        },
        "day": slot.day_of_week,
        "meal_type": slot.meal_type,
        "portions": slot.servings_multiplier,
    }


async def _load_all_recipes_with_ingredients(db: AsyncSession) -> list[Recipe]:
    """Alle Rezepte, die als Ersatz in Frage kommen.

    Beilagen ('side': Dip, Salat, Rotkohl) sind ausgeschlossen - sonst koennte
    man sich per Tausch ein Rotkohl-Abendessen in den Plan holen.
    """
    stmt = (
        select(Recipe)
        .where(Recipe.recipe_role == "main")
        .options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def swap_slot_recipe(
    db: AsyncSession,
    user_id: str,
    plan_id: UUID,
    slot_id: UUID,
    requested_recipe_id: Optional[UUID] = None,
) -> dict:
    """Tauscht das Rezept eines MealSlots und liefert den aktualisierten Slot.

    Raises:
        HTTPException 404: Plan/Slot/Rezept nicht gefunden.
        HTTPException 403: Plan gehört nicht zum Haushalt des Users (IDOR).
        HTTPException 409: Kein passendes Rezept bzw. gewähltes Rezept
                           verletzt Diet-/Allergen-Constraints.
    """
    # ── 1. Owner-Check (IDOR) ────────────────────────────────────────────
    plan_repo = MonthlyPlanRepository(db)
    plan = await plan_repo.get(plan_id)
    await require_plan_owner(db, user_id, plan)
    assert plan is not None  # require_plan_owner raises 404 when None

    # ── 2. Slot laden + Zugehörigkeit prüfen ─────────────────────────────
    slot_repo = MealSlotRepository(db)
    slot = await slot_repo.get(slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot nicht gefunden.",
        )

    weekly_repo = WeeklyPlanRepository(db)
    weekly = await weekly_repo.get(slot.weekly_plan_id)
    if not weekly or weekly.monthly_plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot gehört nicht zu diesem Plan.",
        )

    # ── 3. Constraints ermitteln (Diet + Allergien) ──────────────────────
    household_repo = HouseholdRepository(db)
    household = await household_repo.get(plan.household_id)
    dietary_profile = (household.dietary_profile or {}) if household else {}

    member_repo = MemberRepository(db)
    members = await member_repo.get_active_by_household(plan.household_id)
    member_allergies: list[str] = []
    for m in members:
        member_allergies.extend(m.allergies or [])
    # Deduplizieren + normalisieren (wie in plan_generator.py)
    member_allergies = sorted({a.strip().lower() for a in member_allergies if a})

    # ── 4. Alle Rezepte laden und filtern (bestehende Logik) ─────────────
    all_recipes = await _load_all_recipes_with_ingredients(db)
    if not all_recipes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Keine Rezepte vorhanden. Bitte zuerst Rezepte anlegen.",
        )

    filtered = _filter_by_diet(all_recipes, dietary_profile)

    if member_allergies and filtered:
        ing_id_to_name, recipe_ing_ids, ing_id_to_cat = _build_ingredient_index(filtered)
        filtered = _filter_by_allergens(
            filtered, member_allergies,
            ing_id_to_name, ing_id_to_cat, recipe_ing_ids,
        )

    if not filtered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Kein passendes Rezept für die Ernährungsweise und Allergien "
                "des Haushalts gefunden. Bitte passe das Profil oder die "
                "Allergien an."
            ),
        )

    # ── 5. Rezepte im aktuellen Plan ermitteln ──────────────────────────
    plan_full = await plan_repo.get_with_weekly(plan_id)
    recipes_in_plan: set[UUID] = set()
    for wp in (plan_full.weekly_plans or []) if plan_full else []:
        for s in (wp.meal_slots or []):
            recipes_in_plan.add(s.recipe_id)

    current_recipe_id = slot.recipe_id

    # Kandidaten: gefiltert, nicht im Plan, nicht das aktuelle Rezept
    candidates = [
        r for r in filtered
        if r.id not in recipes_in_plan and r.id != current_recipe_id
    ]
    # Fallback: gefiltert, nicht das aktuelle Rezept (Wiederholung erlaubt)
    if not candidates:
        candidates = [r for r in filtered if r.id != current_recipe_id]

    # ── 6. Rezept auswählen ─────────────────────────────────────────────
    if requested_recipe_id is not None:
        if requested_recipe_id == current_recipe_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Das gewählte Rezept ist bereits im Slot.",
            )

        requested = next((r for r in all_recipes if r.id == requested_recipe_id), None)
        if requested is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rezept nicht gefunden.",
            )

        if requested.id not in {r.id for r in filtered}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Das gewählte Rezept erfüllt die Ernährungsweise oder "
                    "Allergie-Anforderungen des Haushalts nicht."
                ),
            )
        selected = requested
    else:
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Kein passendes alternatives Rezept gefunden. "
                    "Bitte passe die Filter an oder lege neue Rezepte an."
                ),
            )
        # Bevorzugt: erster Kandidat, der nicht im Plan vorkommt
        selected = candidates[0]

    # ── 7. Slot aktualisieren ───────────────────────────────────────────
    slot.recipe_id = selected.id
    await db.flush()

    # Task 74: Einkaufslisten tragen die ISO-Kalenderwoche, nicht den internen
    # Monatszähler (weekly.week_number, 1..5). Maßgeblich ist – genau wie im
    # Generator (plan_generator.py) – das Startdatum der Woche, damit Swap und
    # Neu-Generierung dieselbe KW erzeugen. Das Slot-Datum ist ungeeignet:
    # day_of_week zählt relativ zum Startdatum und kann in einer anderen
    # ISO-Woche landen (z. B. Woche ab Do 31.12.2026, Slot Tag 5 = Mo 04.01.2027).
    _iso_year, iso_week = iso_year_week(weekly.start_date)
    if iso_week is None:
        # Altbestand ohne Startdatum: einzige verfügbare Information.
        iso_week = weekly.week_number
    # Hinweis: weekly.week_number bleibt der interne Wochenzähler (1..5).

    # ── 8. Einkaufsliste der betroffenen Woche invalidieren/neu erzeugen
    # Da das Modell kein "stale"-Flag hat: bestehende Liste + Items der
    # Woche löschen und neu generieren. So bleibt die Liste korrekt.
    gl_repo = GroceryListRepository(db)
    existing_lists = await gl_repo.get_by_plan(plan_id, week_number=iso_week)
    for gl in existing_lists:
        await db.execute(
            sa_delete(GroceryItem).where(GroceryItem.grocery_list_id == gl.id)
        )
        await db.execute(sa_delete(GroceryList).where(GroceryList.id == gl.id))
    await db.flush()

    weekly_full = await weekly_repo.get_with_slots(weekly.id)
    if weekly_full:
        await generate_and_persist_grocery_list(
            weekly_full, db,
            household_id=plan.household_id,
            monthly_plan_id=plan_id,
            week_number=iso_week,
        )

    # Kein commit hier: die Route bzw. die get_db-Dependency committet.
    # So bleibt die Funktion testbar (Rollback im Test-Fixture).
    await db.flush()
    await db.refresh(slot)

    return _slot_payload(slot, selected)
