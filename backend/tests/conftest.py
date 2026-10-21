"""Pytest-Konfiguration und gemeinsame Fixtures"""
import uuid

import pytest

from app.services.plan_generator import GeneratorConfig


@pytest.fixture
def sample_household_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_member_ids() -> list[uuid.UUID]:
    return [
        uuid.UUID("00000000-0000-0000-0000-000000000010"),  # Erwachsener
        uuid.UUID("00000000-0000-0000-0000-000000000011"),  # Kind
    ]


@pytest.fixture
def sample_recipe_ids() -> list[uuid.UUID]:
    """6 Rezepte für einen Monatsplan (reicht für 4 Wochen mit CookOnce)."""
    return [
        uuid.UUID("00000000-0000-0000-0000-000000000100"),
        uuid.UUID("00000000-0000-0000-0000-000000000101"),
        uuid.UUID("00000000-0000-0000-0000-000000000102"),
        uuid.UUID("00000000-0000-0000-0000-000000000103"),
        uuid.UUID("00000000-0000-0000-0000-000000000104"),
        uuid.UUID("00000000-0000-0000-0000-000000000105"),
    ]


@pytest.fixture
def basic_config(sample_household_id, sample_member_ids, sample_recipe_ids) -> GeneratorConfig:
    return GeneratorConfig(
        household_id=sample_household_id,
        month=3,
        year=2025,
        member_ids=sample_member_ids,
        recipe_ids=sample_recipe_ids,
        cook_once_eat_twice_count=2,
        meals_per_week=5,
        include_breakfast=False,
        focus_tags=["schnell", "familie"],
    )