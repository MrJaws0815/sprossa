"""Sprossa family API – minimal & stabil (alle Routen mit get_db)."""
from uuid import UUID
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as t

from app.core.database import get_db
from app.core.dependencies import get_current_user_id

router = APIRouter(tags=["family"], dependencies=[Depends(get_current_user_id)])

class MonthlyPlanCreate(BaseModel):
    month: int; year: int; focus_tags: Optional[list[str]] = None
class HouseholdUpdate(BaseModel):
    name: Optional[str] = None
    dietary_profile: Optional[dict] = None
class HouseholdCreate(BaseModel):
    name: str
class MemberCreate(BaseModel):
    name: str; age: Optional[int] = None

# ─── Plan ──────────────────────────────────────────────────────────────────

@router.post("/plans/generate", status_code=201)
async def generate_plan(
    body: MonthlyPlanCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from app.models.database import MonthlyPlan, WeeklyPlan, MealSlot, GroceryList, GroceryItem

    rows = (await db.execute(t("SELECT id FROM households WHERE user_id=:u"), {"u": UUID(user_id)})).fetchall()
    if not rows: raise HTTPException(400, "No household")
    hid = rows[0][0]

    # ── Task 1: Delete existing plan for same month/year (CASCADE handled by ORM) ──
    existing = await db.execute(
        t("SELECT id FROM monthly_plans WHERE household_id=:hid AND month=:m AND year=:y"),
        {"hid": hid, "m": body.month, "y": body.year},
    )
    existing_row = existing.fetchone()
    if existing_row:
        mp_obj = await db.get(MonthlyPlan, existing_row[0])
        if mp_obj:
            await db.delete(mp_obj)
            await db.flush()

    r = await db.execute(t("SELECT id FROM recipes"))
    rids = [row[0] for row in r.fetchall()]
    if not rids: raise HTTPException(400, "No recipes")

    mp = MonthlyPlan(household_id=hid, month=body.month, year=body.year, status="active")
    db.add(mp); await db.flush()
    fd = date(body.year, body.month, 1)

    all_recipe_ids = []
    for w in range(4):
        wp = WeeklyPlan(household_id=hid, monthly_plan_id=mp.id, week_number=w+1, start_date=fd+timedelta(weeks=w))
        db.add(wp); await db.flush()
        for d in range(7):
            rid = rids[(w * 7 + d) % len(rids)]
            db.add(MealSlot(weekly_plan_id=wp.id, day_of_week=d+1, meal_type="dinner", recipe_id=rid, is_repeat=False))
            all_recipe_ids.append(rid)

    await db.commit()
    await db.refresh(mp)

    # ── Task 2: Auto-Grocery – aggregiere ALLE Zutaten des neuen Plans ──
    unique_rids = list(set(all_recipe_ids))
    grocery_info = None
    if unique_rids:
        items = (
            await db.execute(
                t("""SELECT ri.ingredient_id, SUM(ri.quantity), ri.unit, i.category, i.name
FROM recipe_ingredients ri JOIN ingredients i ON i.id=ri.ingredient_id
WHERE ri.recipe_id=ANY(:rids) GROUP BY ri.ingredient_id, ri.unit, i.category, i.name"""),
                {"rids": unique_rids},
            )
        ).fetchall()
        if items:
            gl = GroceryList(household_id=hid, monthly_plan_id=mp.id, week_number=None, is_master_list=True)
            db.add(gl); await db.flush()
            for ing_id, qty, unit, cat, name in items:
                db.add(GroceryItem(grocery_list_id=gl.id, ingredient_id=ing_id, quantity_total=qty, unit=unit, category_override=cat, notes=name))
            await db.commit()
            grocery_info = {"grocery_list_id": str(gl.id), "items": len(items)}

    return {
        "plan_id": str(mp.id),
        "month": body.month,
        "year": body.year,
        "status": "active",
        "weeks": 4,
        "grocery_list": grocery_info,
    }

@router.get("/plans")
async def list_plans(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(t("SELECT id, month, year, status FROM monthly_plans ORDER BY year DESC, month DESC"))
    return [{"id": str(row[0]), "month": row[1], "year": row[2], "status": row[3]} for row in r.fetchall()]

@router.get("/plans/current-and-next")
async def current_and_next_plans(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    today = date.today()
    months = [(today.month, today.year)]
    if today.month == 12:
        months.append((1, today.year + 1))
    else:
        months.append((today.month + 1, today.year))
    r = await db.execute(
        t("SELECT id, month, year, status FROM monthly_plans WHERE (month=:m1 AND year=:y1) OR (month=:m2 AND year=:y2) ORDER BY year, month"),
        {"m1": months[0][0], "y1": months[0][1], "m2": months[1][0], "y2": months[1][1]},
    )
    return [{"id": str(row[0]), "month": row[1], "year": row[2], "status": row[3]} for row in r.fetchall()]

@router.get("/plans/upcoming")
async def upcoming_plans(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    today = date.today()
    r = await db.execute(
        t("SELECT id, month, year, status FROM monthly_plans WHERE year > :y OR (year = :y AND month >= :m) ORDER BY year, month"),
        {"y": today.year, "m": today.month},
    )
    return [{"id": str(row[0]), "month": row[1], "year": row[2], "status": row[3]} for row in r.fetchall()]

@router.get("/plans/{plan_id}/weeks")
async def list_weeks(plan_id: UUID, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    weeks = (await db.execute(t("SELECT id, week_number, start_date, EXTRACT(WEEK FROM start_date)::int AS cw FROM weekly_plans WHERE monthly_plan_id=:pid ORDER BY week_number"), {"pid": plan_id})).fetchall()
    result = []
    for w in weeks:
        slots = (await db.execute(t("""SELECT ms.id, ms.day_of_week, ms.meal_type, ms.recipe_id, ms.is_repeat, r.title, r.kid_friendly_tip, r.difficulty
            FROM meal_slots ms LEFT JOIN recipes r ON r.id = ms.recipe_id
            WHERE ms.weekly_plan_id=:wid ORDER BY ms.day_of_week"""), {"wid": w[0]})).fetchall()
        result.append({"id": str(w[0]), "week_number": w[1], "start_date": str(w[2]) if w[2] else None,
            "cw": int(w[3]) if w[2] else None,
            "meal_slots": [{"id": str(s[0]), "day_of_week": s[1], "meal_type": s[2], "recipe_id": str(s[3]),
              "is_repeat": s[4], "recipe_title": s[5] or "(kein Rezept)", "kid_friendly_tip": s[6], "difficulty": s[7]} for s in slots]})
    return result

# ─── Recipes ───────────────────────────────────────────────────────────────

@router.get("/recipes")
async def list_recipes(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(t("SELECT id, title, description, servings, prep_time_minutes, cook_time_minutes, difficulty, cook_once_eat_twice, tags, kid_friendly_tip FROM recipes ORDER BY title"))
    return [{"id": str(row[0]), "title": row[1], "description": row[2], "servings": row[3],
             "prep_time_minutes": row[4], "cook_time_minutes": row[5], "difficulty": row[6],
             "cook_once_eat_twice": row[7], "tags": row[8] or [], "kid_friendly_tip": row[9]} for row in r.fetchall()]

# ─── Grocery ───────────────────────────────────────────────────────────────

@router.post("/grocery/generate", status_code=201)
async def generate_grocery(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    from app.models.database import GroceryList, GroceryItem
    from collections import defaultdict
    plans = (await db.execute(t("SELECT id, household_id FROM monthly_plans ORDER BY year DESC, month DESC LIMIT 1"))).fetchall()
    if not plans: raise HTTPException(400, "No plans - generate a plan first")
    pid, hid = plans[0][0], plans[0][1]
    weekly = (await db.execute(t("SELECT id FROM weekly_plans WHERE monthly_plan_id=:pid ORDER BY week_number LIMIT 1"), {"pid": pid})).fetchall()
    if not weekly: raise HTTPException(400, "No weekly plans")
    slots = (await db.execute(t("SELECT recipe_id FROM meal_slots WHERE weekly_plan_id=:wid AND is_repeat=false"), {"wid": weekly[0][0]})).fetchall()
    rids = list(set([s[0] for s in slots]))
    items = (await db.execute(t("""SELECT ri.ingredient_id, SUM(ri.quantity), ri.unit, i.category, i.name
FROM recipe_ingredients ri JOIN ingredients i ON i.id=ri.ingredient_id
WHERE ri.recipe_id=ANY(:rids) GROUP BY ri.ingredient_id, ri.unit, i.category, i.name"""), {"rids": rids})).fetchall()
    if not items: raise HTTPException(400, "No ingredients")
    gl = GroceryList(household_id=hid, week_number=1)
    db.add(gl); await db.flush()
    for ing_id, qty, unit, cat, name in items:
        db.add(GroceryItem(grocery_list_id=gl.id, ingredient_id=ing_id, quantity_total=qty, unit=unit, category_override=cat, notes=name))
    await db.commit()
    return {"grocery_list_id": str(gl.id), "items": len(items)}

@router.get("/grocery-lists")
async def list_grocery_lists(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    # Supermarkt aus dietary_profile lesen
    rows = await db.execute(t("SELECT dietary_profile FROM households WHERE user_id=:u"), {"u": UUID(user_id)})
    dp = rows.scalar() or {}
    supermarket = dp.get("preferred_supermarket", "Rewe") if isinstance(dp, dict) else "Rewe"
    r = await db.execute(t("SELECT id, week_number FROM grocery_lists ORDER BY generated_at DESC"))
    return [{"id": str(row[0]), "week_number": row[1], "supermarket": supermarket, "items": []} for row in r.fetchall()]

@router.get("/grocery-lists/{list_id}")
async def get_grocery_list(list_id: UUID, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    gl = (await db.execute(t("SELECT id, week_number FROM grocery_lists WHERE id=:lid"), {"lid": list_id})).fetchone()
    if not gl: raise HTTPException(404)
    items = (await db.execute(t("SELECT id, quantity_total, unit, is_checked, category_override, notes FROM grocery_items WHERE grocery_list_id=:lid ORDER BY category_override"), {"lid": list_id})).fetchall()
    return {"id": str(gl[0]), "week_number": gl[1],
            "items": [{"id": str(i[0]), "ingredient_name": i[5], "quantity_total": i[1], "unit": i[2], "category": i[4], "is_checked": i[3]} for i in items]}

# ─── Household ─────────────────────────────────────────────────────────────

@router.get("/households")
async def list_households(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(t("SELECT id, name, dietary_profile FROM households WHERE user_id=:u"), {"u": UUID(user_id)})
    return [{"id": str(row[0]), "name": row[1], "dietary_profile": row[2] or {}} for row in r.fetchall()]

@router.put("/households/{hid}")
async def update_household(hid: UUID, body: HouseholdUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    updates = []
    params = {"hid": hid, "u": UUID(user_id)}
    if body.name is not None:
        updates.append("name=:name")
        params["name"] = body.name
    if body.dietary_profile is not None:
        updates.append("dietary_profile=:dp")
        params["dp"] = body.dietary_profile
    if updates:
        await db.execute(t(f"UPDATE households SET {', '.join(updates)} WHERE id=:hid AND user_id=:u"), params)
        await db.commit()
    return {"status": "ok"}

@router.get("/households/{hid}/members")
async def list_members(hid: UUID, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    r = await db.execute(t("SELECT id, name, age FROM members WHERE household_id=:hid ORDER BY age DESC"), {"hid": hid})
    return [{"id": str(row[0]), "name": row[1], "age": row[2]} for row in r.fetchall()]

@router.post("/households/{hid}/members", status_code=201)
async def add_member(hid: UUID, body: MemberCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    from app.models.database import Member
    m = Member(household_id=hid, name=body.name, age=body.age)
    db.add(m); await db.flush(); await db.refresh(m)
    await db.commit()
    return {"id": str(m.id), "name": m.name, "age": m.age}

@router.delete("/households/{hid}/members/{mid}")
async def remove_member(hid: UUID, mid: UUID, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await db.execute(t("DELETE FROM members WHERE id=:mid AND household_id=:hid"), {"mid": mid, "hid": hid})
    await db.commit()
    return {"status": "deleted"}

@router.get("/recipes/{recipe_id}")
async def get_recipe_detail(
    recipe_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    r = (await db.execute(t("""SELECT id, title, description, servings, prep_time_minutes,
        cook_time_minutes, difficulty, instructions, cook_once_eat_twice,
        tags, kid_friendly_tip FROM recipes WHERE id=:rid"""), {"rid": recipe_id})).fetchone()
    if not r: raise HTTPException(404)
    ing = (await db.execute(t("""SELECT i.name, ri.quantity, ri.unit, i.category
        FROM recipe_ingredients ri JOIN ingredients i ON i.id=ri.ingredient_id
        WHERE ri.recipe_id=:rid ORDER BY i.category, i.name"""), {"rid": recipe_id})).fetchall()
    return {
        "id": str(r[0]), "title": r[1], "description": r[2], "servings": r[3],
        "prep_time_minutes": r[4], "cook_time_minutes": r[5], "difficulty": r[6],
        "instructions": r[7], "cook_once_eat_twice": r[8], "tags": r[9] or [],
        "kid_friendly_tip": r[10],
        "ingredients": [{"name": i[0], "quantity": i[1], "unit": i[2], "category": i[3]} for i in ing],
    }

@router.post("/households", status_code=201)
async def create_household(
    body: "HouseholdCreate",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from app.models.database import Household
    h = Household(name=body.name, user_id=UUID(user_id))
    db.add(h); await db.flush(); await db.refresh(h); await db.commit()
    return {"id": str(h.id), "name": h.name}
