"""Tests für die harte Validierung von shopping_days (Task 3).

Die Validierung sitzt in app/schemas/api.py (HouseholdUpdate), damit sie
sowohl bei PUT /households/{hid} als auch bei PATCH greift.
"""
import pytest
from pydantic import ValidationError

from app.schemas.api import HouseholdUpdate


def test_shopping_days_empty_with_non_master_frequency_raises():
    with pytest.raises(ValidationError) as exc:
        HouseholdUpdate(
            dietary_profile={"shopping_frequency": "1x_woche", "shopping_days": []}
        )
    assert "Mindestens ein Einkaufstag muss ausgewaehlt werden." in str(exc.value)


def test_shopping_days_empty_with_nach_bedarf_allowed():
    update = HouseholdUpdate(
        dietary_profile={"shopping_frequency": "nach_bedarf", "shopping_days": []}
    )
    assert update.dietary_profile["shopping_days"] == []


def test_shopping_days_empty_with_none_frequency_allowed():
    update = HouseholdUpdate(dietary_profile={"shopping_days": []})
    assert update.dietary_profile["shopping_days"] == []


def test_shopping_days_duplicates_raise():
    with pytest.raises(ValidationError) as exc:
        HouseholdUpdate(
            dietary_profile={"shopping_frequency": "1x_woche", "shopping_days": [1, 1]}
        )
    assert "Einkaufstage duerfen nicht doppelt vorkommen." in str(exc.value)


def test_shopping_days_out_of_range_raise():
    with pytest.raises(ValidationError) as exc:
        HouseholdUpdate(
            dietary_profile={"shopping_frequency": "1x_woche", "shopping_days": [0, 8]}
        )
    assert "Einkaufstage muessen zwischen 1 und 7 liegen." in str(exc.value)


def test_shopping_days_valid():
    update = HouseholdUpdate(
        dietary_profile={"shopping_frequency": "1x_woche", "shopping_days": [1, 3, 5]}
    )
    assert update.dietary_profile["shopping_days"] == [1, 3, 5]
