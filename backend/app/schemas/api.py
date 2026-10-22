"""Pydantic-Schemas für die API (Request/Response)"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
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


class HouseholdOut(BaseModel):
    id: UUID
    name: str
    dietary_profile: Optional[dict] = {}
    created_at: datetime

    class Config:
        from_attributes = True


# -- Member -----------------------------------------------------------------

class MemberCreate(BaseModel):
    name: str
    age: Optional[int] = None
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


class RecipeOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    servings: int
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    difficulty: str
    kid_friendly_tip: Optional[str] = None
    cook_once_eat_twice: bool
    tags: Optional[list[str]] = []
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
    week_number: int = Field(ge=1, le=5)
    start_date: Optional[date] = None
    meal_slots: list[MealSlotCreate] = []


class MonthlyPlanCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int
    focus_tags: Optional[list[str]] = []


class MonthlyPlanOut(BaseModel):
    id: UUID
    household_id: UUID
    month: int
    year: int
    status: str
    focus_tags: Optional[list[str]] = []
    generated_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# -- WeeklyPlan / MealSlot --------------------------------------------------

class MealSlotOut(BaseModel):
    id: UUID
    day_of_week: int
    meal_type: str
    recipe_id: UUID
    servings_multiplier: float
    is_repeat: bool

    class Config:
        from_attributes = True


class WeeklyPlanOut(BaseModel):
    id: UUID
    week_number: int
    start_date: Optional[date] = None
    meal_slots: list[MealSlotOut] = []
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# -- Household Update --------------------------------------------------------

class HouseholdUpdate(BaseModel):
    name: Optional[str] = None
    dietary_profile: Optional[dict] = None


# -- Grocery ----------------------------------------------------------------

class GroceryItemOut(BaseModel):
    id: UUID
    ingredient_name: str
    category: str
    quantity_total: float
    unit: str
    is_checked: bool
    notes: Optional[str] = None


class GroceryListOut(BaseModel):
    id: UUID
    week_number: Optional[int] = None
    is_master_list: bool
    generated_at: datetime
    supermarket: str = "Rewe"
    items: list[GroceryItemOut] = []