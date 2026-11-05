"""Pydantic-Schemas für die API (Request/Response)"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, model_validator
from enum import Enum


# -- Enums ------------------------------------------------------------------

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    advanced = "advanced"


class PlanStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


# -- User -------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -- Household --------------------------------------------------------------

class HouseholdCreate(BaseModel):
    name: str
    dietary_profile: Optional[dict] = {}
    # Art. 9 DSGVO: Einwilligung in die Verarbeitung von Gesundheitsdaten (Allergien).
    # Der Server setzt daraus einen Zeitstempel; das Flag selbst wird nicht gespeichert.
    health_data_consent: bool = False


class HouseholdOut(BaseModel):
    id: UUID
    name: str
    dietary_profile: Optional[dict] = {}
    health_data_consent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# -- Member -----------------------------------------------------------------

class MemberCreate(BaseModel):
    name: str
    age: Optional[int] = Field(default=None, ge=0, le=120)
    weight_kg: Optional[float] = None
    allergies: Optional[list[str]] = []
    dietary_goals: Optional[dict] = {}
    notes: Optional[str] = None
    is_active: bool = True


class MemberOut(BaseModel):
    id: UUID
    household_id: UUID
    name: str
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    allergies: Optional[list[str]] = []
    dietary_goals: Optional[dict] = {}
    notes: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# -- Ingredient -------------------------------------------------------------

class IngredientCreate(BaseModel):
    name: str
    category: str
    unit_default: str = "Stück"
    storage: Optional[str] = None


class IngredientOut(BaseModel):
    id: UUID
    name: str
    category: str
    unit_default: str
    storage: Optional[str] = None

    class Config:
        from_attributes = True


# -- Recipe -----------------------------------------------------------------

class RecipeIngredientCreate(BaseModel):
    ingredient_id: UUID
    quantity: float
    unit: str
    is_optional: bool = False
    substitution_ingredient_id: Optional[UUID] = None
    substitution_note: Optional[str] = None


class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    servings: int = 4
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    difficulty: str = "easy"
    instructions: Optional[str] = None
    kid_friendly_tip: Optional[str] = None
    cook_once_eat_twice: bool = False
    tags: Optional[list[str]] = []
    ingredients: list[RecipeIngredientCreate] = []


class RecipeIngredientOut(BaseModel):
    id: UUID
    ingredient_id: UUID
    ingredient_name: Optional[str] = None
    # Frontend liest `name` / `category`; ingredient_name bleibt aus Kompatibilität.
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: float
    unit: str
    is_optional: bool = False
    substitution_note: Optional[str] = None


class RecipeOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    servings: float
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    difficulty: str
    instructions: Optional[str] = None
    kid_friendly_tip: Optional[str] = None
    cook_once_eat_twice: bool
    tags: Optional[list[str]] = []
    ingredients: list[RecipeIngredientOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


# -- Plans ------------------------------------------------------------------

class MealSlotCreate(BaseModel):
    day_of_week: int = Field(ge=1, le=7)
    meal_type: str
    recipe_id: UUID
    servings_multiplier: float = 1.0
    is_repeat: bool = False


class WeeklyPlanCreate(BaseModel):
    week_number: int = Field(ge=1, le=53)
    start_date: Optional[date] = None
    meal_slots: list[MealSlotCreate] = []


class MonthlyPlanCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int
    focus_tags: Optional[list[str]] = []

    @model_validator(mode="after")
    def _validate_month_scope(self):
        """Nur aktueller oder naechster Monat ist planbar (Jahresueberlauf beachten)."""
        today = date.today()
        if today.month == 12:
            next_month, next_year = 1, today.year + 1
        else:
            next_month, next_year = today.month + 1, today.year
        allowed = {(today.year, today.month), (next_year, next_month)}
        if (self.year, self.month) not in allowed:
            raise ValueError(
                "Plaene koennen nur fuer den aktuellen oder naechsten Monat "
                "erstellt werden."
            )
        return self


class MonthlyPlanOut(BaseModel):
    id: UUID
    household_id: UUID
    month: int
    year: int
    month_name: str = ""  # deutscher Monatsname, z.B. "Oktober"
    weeks_count: int = 0
    recipe_count: int = 0  # distinct Rezepte im Plan
    status: str
    focus_tags: Optional[list[str]] = []
    generated_at: Optional[datetime] = None
    notes: Optional[str] = None
    total_portions: Optional[float] = None

    class Config:
        from_attributes = True


# -- WeeklyPlan / MealSlot --------------------------------------------------

class MealSlotOut(BaseModel):
    id: UUID
    day_of_week: int
    meal_type: str
    recipe_id: UUID
    recipe_title: Optional[str] = None
    recipe_servings: Optional[int] = None
    servings_multiplier: float
    is_repeat: bool

    class Config:
        from_attributes = True


class WeeklyPlanOut(BaseModel):
    id: UUID
    week_number: int
    start_date: Optional[date] = None
    cw: Optional[int] = None  # Kalenderwoche (ISO), vom Backend berechnet
    meal_slots: list[MealSlotOut] = []
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# -- Household Update --------------------------------------------------------

class HouseholdUpdate(BaseModel):
    name: Optional[str] = None
    dietary_profile: Optional[dict] = None
    # Art. 9 DSGVO: Einwilligung in Gesundheitsdaten (Allergien). True setzt einmalig
    # den Zeitstempel; False widerruft (Zeitstempel bleibt als Nachweis erhalten).
    health_data_consent: Optional[bool] = None
    health_data_consent_revoked: Optional[bool] = None

    @model_validator(mode="after")
    def _validate_shopping_days(self):
        """Task 74/75: Mindestens ein Einkaufstag bei Nicht-Master-Liste.

        - `shopping_frequency` "nach_bedarf" (oder leer/fehlend) = Master-Liste:
          leere `shopping_days` sind erlaubt.
        - Sonst: Liste muss mindestens 1 Eintrag haben, Werte 1..7,
          keine Duplikate.
        """
        if self.dietary_profile is None:
            return self
        dp = self.dietary_profile
        shopping_days = dp.get("shopping_days")
        shopping_frequency = dp.get("shopping_frequency")

        # Master-Liste: keine Pflicht (konsistent mit plan_generator.py)
        is_master = shopping_frequency in (None, "", "nach_bedarf")

        if shopping_days is not None and not is_master:
            if not isinstance(shopping_days, list):
                raise ValueError("shopping_days muss eine Liste sein.")
            if len(shopping_days) < 1:
                raise ValueError("Mindestens ein Einkaufstag muss ausgewaehlt werden.")
            normalized = []
            for day in shopping_days:
                try:
                    d = int(day)
                except (TypeError, ValueError):
                    raise ValueError("Einkaufstage muessen zwischen 1 und 7 liegen.")
                if not (1 <= d <= 7):
                    raise ValueError("Einkaufstage muessen zwischen 1 und 7 liegen.")
                normalized.append(d)
            if len(normalized) != len(set(normalized)):
                raise ValueError("Einkaufstage duerfen nicht doppelt vorkommen.")
        return self


# -- Grocery ----------------------------------------------------------------

class GroceryItemOut(BaseModel):
    id: UUID
    ingredient_name: str
    category: str
    quantity_total: float
    unit: str
    is_checked: bool
    notes: Optional[str] = None
    # Task 81: Varianten-Info (z. B. "festkochend, mehligkochend") –
    # ingredient_name enthält bereits den zusammengesetzten Anzeigenamen.
    variants: Optional[list[str]] = None


class GroceryListOut(BaseModel):
    id: UUID
    week_number: Optional[int] = None
    cw: Optional[int] = None  # ISO-Kalenderwoche (Alias zu week_number nach Task 61)
    is_master_list: bool
    generated_at: datetime
    supermarket: str = "Rewe"
    # Task 85: Segment-Label (z. B. "Einkauf Mo bis Mi"). Kein DB-Feld;
    # wird aus shopping_days abgeleitet bzw. vom Generator mitgegeben.
    segment_label: Optional[str] = None
    items: list[GroceryItemOut] = []