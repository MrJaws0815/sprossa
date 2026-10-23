"""SQLAlchemy-Datenbankmodelle für Monatsmenü"""
import uuid
from datetime import date, datetime, UTC
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# -- Utility ----------------------------------------------------------------

def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _utcnow() -> datetime:
    return datetime.now(UTC)


# -- Enums ------------------------------------------------------------------

MealType = Enum(
    "breakfast", "lunch", "dinner", "snack",
    name="meal_type",
)

Difficulty = Enum(
    "easy", "medium", "advanced",
    name="difficulty",
)

PlanStatus = Enum(
    "draft", "active", "archived",
    name="plan_status",
)

IngredientCategory = Enum(
    "vegetables", "fruit", "meat", "dairy", "grains",
    "spices", "canned", "frozen", "condiments", "other",
    name="ingredient_category",
)


# -- Tables -----------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    households: Mapped[list["Household"]] = relationship("Household", back_populates="owner")


class Household(Base):
    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    dietary_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="households")
    members: Mapped[list["Member"]] = relationship("Member", back_populates="household", cascade="all, delete-orphan")
    recipes: Mapped[list["Recipe"]] = relationship("Recipe", back_populates="household", cascade="all, delete-orphan")
    weekly_plans: Mapped[list["WeeklyPlan"]] = relationship("WeeklyPlan", back_populates="household", cascade="all, delete-orphan")
    monthly_plans: Mapped[list["MonthlyPlan"]] = relationship("MonthlyPlan", back_populates="household", cascade="all, delete-orphan")
    grocery_lists: Mapped[list["GroceryList"]] = relationship("GroceryList", back_populates="household", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    allergies: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True, default=list)
    dietary_goals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    household: Mapped["Household"] = relationship("Household", back_populates="members")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # stores IngredientCategory values
    unit_default: Mapped[str] = mapped_column(String(20), default="Stück")
    storage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "Kühlschrank", "Vorrat", "Tiefkühler"

    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="ingredient",
        cascade="all, delete-orphan",
        foreign_keys="[RecipeIngredient.ingredient_id]",
    )


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    servings: Mapped[int] = mapped_column(Integer, default=4)
    prep_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    kid_friendly_tip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cook_once_eat_twice: Mapped[bool] = mapped_column(Boolean, default=False)
    leftover_recipe_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=True
    )
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    household: Mapped["Household"] = relationship("Household", back_populates="recipes")
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    substitution_ingredient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=True
    )
    substitution_note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pre_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship(
        "Ingredient", back_populates="recipe_ingredients",
        foreign_keys=[ingredient_id],
    )


class MonthlyPlan(Base):
    __tablename__ = "monthly_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    focus_tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True, default=list)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_portions: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=None)

    household: Mapped["Household"] = relationship("Household", back_populates="monthly_plans")
    weekly_plans: Mapped[list["WeeklyPlan"]] = relationship("WeeklyPlan", back_populates="monthly_plan", cascade="all, delete-orphan")
    grocery_lists: Mapped[list["GroceryList"]] = relationship("GroceryList", back_populates="monthly_plan", cascade="all, delete-orphan")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    monthly_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("monthly_plans.id"), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    household: Mapped["Household"] = relationship("Household", back_populates="weekly_plans")
    monthly_plan: Mapped["MonthlyPlan"] = relationship("MonthlyPlan", back_populates="weekly_plans")
    meal_slots: Mapped[list["MealSlot"]] = relationship("MealSlot", back_populates="weekly_plan", cascade="all, delete-orphan")


class MealSlot(Base):
    __tablename__ = "meal_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    weekly_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weekly_plans.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Monday..7=Sunday
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    recipe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False)
    servings_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    is_repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    original_meal_slot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meal_slots.id"), nullable=True
    )

    weekly_plan: Mapped["WeeklyPlan"] = relationship("WeeklyPlan", back_populates="meal_slots")
    recipe: Mapped["Recipe"] = relationship("Recipe")


class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    household_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("households.id"), nullable=False)
    monthly_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("monthly_plans.id"), nullable=True
    )
    week_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # NULL = Monatsliste
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    is_master_list: Mapped[bool] = mapped_column(Boolean, default=False)

    household: Mapped["Household"] = relationship("Household", back_populates="grocery_lists")
    monthly_plan: Mapped["MonthlyPlan"] = relationship("MonthlyPlan", back_populates="grocery_lists")
    items: Mapped[list["GroceryItem"]] = relationship("GroceryItem", back_populates="grocery_list", cascade="all, delete-orphan")


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    grocery_list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grocery_lists.id"), nullable=False)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False)
    quantity_total: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity_purchased: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    category_override: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    grocery_list: Mapped["GroceryList"] = relationship("GroceryList", back_populates="items")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient")


# ─── Waitlist (persistente Beta-Warteschlange) ──────────────────────────

class WaitlistEntryModel(Base):
    __tablename__ = "waitlist"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    household_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmation_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    confirmation_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)