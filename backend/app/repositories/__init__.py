"""Repository-Interface + In-Memory-Implementierung für Kern-Entities.

Dieses Modul enthält:
1. Alte In-Memory-Dataclasses + Repos (Bestand, von Tests genutzt)
2. Neue async SQLAlchemy-Repos (für Produktion)
3. DI-Factory `get_repository()` für FastAPI-Routen
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, AsyncGenerator, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

# ─── FastAPI-DI: Repo-Factory ────────────────────────────────────────────

from app.core.config import settings
from app.core.database import get_db


async def get_repository(
    repo_type: type,
) -> AsyncGenerator[Any, None]:
    """FastAPI-Dependency: Erzeugt ein Repository mit einer DB-Session.

    Nutzung in Routen:
        repo: UserRepository = Depends(get_repository(UserRepository))
    """
    from app.core.database import get_db

    async for session in get_db():
        yield repo_type(session)


# ─── Dataclasses (In-Memory, für Tests) ──────────────────────────────────

@dataclass
class UserRecord:
    email: str
    password_hash: str
    display_name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    is_active: bool = True
    stripe_customer_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HouseholdRecord:
    name: str
    user_id: str
    dietary_profile: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MemberRecord:
    household_id: str
    name: str
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    allergies: list = field(default_factory=list)
    dietary_goals: dict = field(default_factory=dict)
    notes: Optional[str] = None
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class RecipeRecord:
    household_id: str
    title: str
    description: Optional[str] = None
    servings: int = 4
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    difficulty: str = "easy"
    instructions: Optional[str] = None
    cook_once_eat_twice: bool = False
    tags: list = field(default_factory=list)
    kid_friendly_tip: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class IngredientRecord:
    name: str
    category: str
    unit_default: str = "Stück"
    storage: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class WaitlistEntry:
    email: str
    name: Optional[str] = None
    household_size: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    confirmation_token: Optional[str] = None
    confirmation_sent_at: Optional[datetime] = None
    confirmed_ip: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# ─── Repository-Interfaces (In-Memory, für Tests) ────────────────────────


class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserRecord]: ...
    @abstractmethod
    def get_by_id(self, uid: str) -> Optional[UserRecord]: ...
    @abstractmethod
    def save(self, user: UserRecord) -> UserRecord: ...


class HouseholdRepository(ABC):
    @abstractmethod
    def get_by_id(self, hid: str) -> Optional[HouseholdRecord]: ...
    @abstractmethod
    def save(self, h: HouseholdRecord) -> HouseholdRecord: ...
    @abstractmethod
    def get_members(self, hid: str) -> list[MemberRecord]: ...
    @abstractmethod
    def save_member(self, m: MemberRecord) -> MemberRecord: ...
    @abstractmethod
    def delete_member(self, mid: str) -> bool: ...


class RecipeRepository(ABC):
    @abstractmethod
    def get_by_id(self, rid: str) -> Optional[RecipeRecord]: ...
    @abstractmethod
    def list_all(self) -> list[RecipeRecord]: ...
    @abstractmethod
    def save(self, r: RecipeRecord) -> RecipeRecord: ...


class IngredientRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[IngredientRecord]: ...
    @abstractmethod
    def save(self, i: IngredientRecord) -> IngredientRecord: ...


class WaitlistRepositoryABC(ABC):
    @abstractmethod
    def save(self, entry: WaitlistEntry) -> WaitlistEntry: ...
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[WaitlistEntry]: ...


# ─── In-Memory-Implementierung ───────────────────────────────────────────


class InMemoryUserRepo(UserRepository):
    def __init__(self):
        self._store: dict[str, UserRecord] = {}
        self._email_index: dict[str, str] = {}

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        uid = self._email_index.get(email)
        return self._store.get(uid) if uid else None

    def get_by_id(self, uid: str) -> Optional[UserRecord]:
        return self._store.get(uid)

    def save(self, user: UserRecord) -> UserRecord:
        self._store[user.id] = user
        self._email_index[user.email] = user.id
        return user


class InMemoryHouseholdRepo(HouseholdRepository):
    def __init__(self):
        self._store: dict[str, HouseholdRecord] = {}
        self._members: dict[str, MemberRecord] = {}

    def get_by_id(self, hid: str) -> Optional[HouseholdRecord]:
        return self._store.get(hid)

    def save(self, h: HouseholdRecord) -> HouseholdRecord:
        self._store[h.id] = h
        return h

    def get_members(self, hid: str) -> list[MemberRecord]:
        return [m for m in self._members.values() if m.household_id == hid]

    def save_member(self, m: MemberRecord) -> MemberRecord:
        self._members[m.id] = m
        return m

    def delete_member(self, mid: str) -> bool:
        if mid in self._members:
            del self._members[mid]
            return True
        return False


class InMemoryRecipeRepo(RecipeRepository):
    def __init__(self):
        self._store: dict[str, RecipeRecord] = {}

    def get_by_id(self, rid: str) -> Optional[RecipeRecord]:
        return self._store.get(rid)

    def list_all(self) -> list[RecipeRecord]:
        return list(self._store.values())

    def save(self, r: RecipeRecord) -> RecipeRecord:
        self._store[r.id] = r
        return r


class InMemoryIngredientRepo(IngredientRepository):
    def __init__(self):
        self._store: dict[str, IngredientRecord] = {}

    def list_all(self) -> list[IngredientRecord]:
        return list(self._store.values())

    def save(self, i: IngredientRecord) -> IngredientRecord:
        self._store[i.id] = i
        return i


class InMemoryWaitlistRepo(WaitlistRepositoryABC):
    def __init__(self):
        self._store: dict[str, WaitlistEntry] = {}
        self._email_index: dict[str, str] = {}

    def save(self, entry: WaitlistEntry) -> WaitlistEntry:
        self._store[entry.id] = entry
        self._email_index[entry.email] = entry.id
        return entry

    def get_by_email(self, email: str) -> Optional[WaitlistEntry]:
        eid = self._email_index.get(email)
        return self._store.get(eid) if eid else None


# ─── Neue async SQLAlchemy-Repos (für Produktion) ────────────────────────

from app.repositories.base import BaseRepository  # noqa: E402, F811
from app.repositories.user import UserRepository as UserRepoDB  # noqa: E402, F811
from app.repositories.household import HouseholdRepository as HouseholdRepoDB  # noqa: E402, F811
from app.repositories.member import MemberRepository as MemberRepoDB  # noqa: E402, F811
from app.repositories.recipe import RecipeRepository as RecipeRepoDB  # noqa: E402, F811
from app.repositories.ingredient import IngredientRepository as IngredientRepoDB  # noqa: E402, F811
from app.repositories.plan import (  # noqa: E402, F811
    WeeklyPlanRepository as WeeklyPlanRepoDB,
    MonthlyPlanRepository as MonthlyPlanRepoDB,
    MealSlotRepository as MealSlotRepoDB,
)
from app.repositories.grocery import (  # noqa: E402, F811
    GroceryListRepository as GroceryListRepoDB,
    GroceryItemRepository as GroceryItemRepoDB,
)
from app.repositories.waitlist import WaitlistRepository as WaitlistRepoDB  # noqa: E402, F811