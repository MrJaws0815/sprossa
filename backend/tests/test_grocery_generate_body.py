"""Task 54: POST /grocery/generate muss den Body respektieren.

Vorher wurde `weekly_plan_id` ausschließlich als Query-Parameter gelesen.
Ein Body {"plan_id": ...} wurde still verworfen und der Endpunkt befüllte
den *neuesten* Plan des Haushalts — mit HTTP 201, also ohne erkennbaren
Fehler. Diese Tests sichern die Vertragsregeln des Bodys ab.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.routes.family import GroceryGenerateRequest


def test_body_accepts_plan_id():
    pid = uuid.uuid4()
    assert GroceryGenerateRequest(plan_id=pid).plan_id == pid


def test_body_accepts_monthly_plan_id_alias():
    pid = uuid.uuid4()
    assert GroceryGenerateRequest(monthly_plan_id=pid).monthly_plan_id == pid


def test_body_accepts_uuid_string():
    pid = str(uuid.uuid4())
    assert str(GroceryGenerateRequest(plan_id=pid).plan_id) == pid


def test_body_is_optional():
    assert GroceryGenerateRequest() is not None


def test_body_rejects_unknown_fields():
    """Ein falsch benannter Parameter darf nicht wieder still ins Leere laufen."""
    with pytest.raises(ValidationError) as exc:
        GroceryGenerateRequest(weekly_plan_id=str(uuid.uuid4()))
    assert exc.value.errors()[0]["type"] == "extra_forbidden"


def test_body_rejects_invalid_uuid():
    with pytest.raises(ValidationError):
        GroceryGenerateRequest(plan_id="keine-uuid")
