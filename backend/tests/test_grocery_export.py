"""Tests für Supermarkt-Gang-Sortierung und Einkaufslisten-Export (Task 33/34).

Deckt ab:
1. Gang-Reihenfolge / Kategorie-Mapping (konfigurierbar)
2. Sortierung von Items, unbekannte Kategorien ans Ende
3. CSV-Inhalt (Semikolon, BOM, Spalten, deutsche Mengen)
4. TXT-Inhalt (Gang-Überschriften, druckbare Zeilen)
5. Export-Route: IDOR/404, Content-Disposition, Formate
"""
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.grocery_engine import (
    GANG_ORDER,
    SUPERMARKET_GANG_ORDER,
    build_export_csv,
    build_export_rows,
    build_export_txt,
    build_grocery_list,
    gang_for_category,
    group_by_gang,
    register_dummy_recipe,
    sort_by_gang,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────

def _item(name, category, qty=1.0, unit="Stück", notes=None, category_override=None):
    """Fake-GroceryItem wie ORM-Objekt inkl. eager ingredient."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        ingredient_id=uuid.uuid4(),
        quantity_total=qty,
        unit=unit,
        is_checked=False,
        category_override=category_override if category_override is not None else category,
        notes=notes,
        ingredient=SimpleNamespace(name=name, category=category),
    )


@pytest.fixture
def export_items():
    """Bewusst in falscher Reihenfolge angelegt."""
    return [
        _item("Tiefkühlpizza", "frozen", 1.0, "Stück"),
        _item("Hähnchenbrust", "meat", 2.0, "Stück"),
        _item("Sahne", "dairy", 200.0, "ml"),
        _item("Karotten", "vegetables", 3.0, "Stück"),
        _item("Äpfel", "fruit", 1.5, "kg"),
        _item("Mehl", "grains", 500.0, "g"),
        _item("Mineralwasser", "beverages", 6.0, "Flasche"),
        _item("Tomaten", "canned", 2.0, "Dose"),
        _item("Pfeffer", "spices", 1.0, "Päckchen"),
        _item("Batterien", "unknown_category_xyz", 4.0, "Stück"),
    ]


# ─── 1. Gang-Reihenfolge ──────────────────────────────────────────────────

class TestGangOrder:
    def test_reihenfolge_entspricht_supermarkt_gang(self):
        """Konstante enthält die geforderte Reihenfolge."""
        assert GANG_ORDER == [
            "Gemüse", "Obst", "Fleisch/Fisch", "Milchprodukte/Eier",
            "Backwaren", "Tiefkühl", "Getränke", "Vorrat/Konserven",
            "Gewürze", "Sonstiges",
        ]
        # Tupel-Form macht Supermarkt-Erweiterung möglich (Slugs je Gang)
        assert all(isinstance(label, str) and isinstance(slugs, tuple)
                   for label, slugs in SUPERMARKET_GANG_ORDER)

    def test_kategorie_mapping(self):
        assert gang_for_category("vegetables") == "Gemüse"
        assert gang_for_category("fruit") == "Obst"
        assert gang_for_category("meat") == "Fleisch/Fisch"
        assert gang_for_category("dairy") == "Milchprodukte/Eier"
        assert gang_for_category("grains") == "Backwaren"
        assert gang_for_category("frozen") == "Tiefkühl"
        assert gang_for_category("beverages") == "Getränke"
        assert gang_for_category("canned") == "Vorrat/Konserven"
        assert gang_for_category("spices") == "Gewürze"
        assert gang_for_category("condiments") == "Vorrat/Konserven"
        assert gang_for_category("other") == "Sonstiges"

    def test_unbekannte_kategorie_ans_ende(self):
        assert gang_for_category("voellig_unbekannt") == "Sonstiges"
        assert gang_for_category(None) == "Sonstiges"
        assert gang_for_category("") == "Sonstiges"

    def test_sortierung_nach_gang(self, export_items):
        names = [i.ingredient.name for i in sort_by_gang(export_items)]
        assert names[0] == "Karotten"          # Gemüse zuerst
        assert names[1] == "Äpfel"             # Obst
        assert names[2] == "Hähnchenbrust"     # Fleisch
        assert names[3] == "Sahne"             # Milchprodukte
        assert names[-1] == "Batterien"        # unbekannt → Sonstiges ans Ende

    def test_gruppierung_lässt_leere_gaenge_aus(self, export_items):
        groups = group_by_gang(export_items)
        labels = [g["gang"] for g in groups]
        assert labels == [
            "Gemüse", "Obst", "Fleisch/Fisch", "Milchprodukte/Eier",
            "Backwaren", "Tiefkühl", "Getränke", "Vorrat/Konserven",
            "Gewürze", "Sonstiges",
        ]
        assert groups[0]["items"][0].ingredient.name == "Karotten"

    def test_eigene_gang_order_konfigurierbar(self, export_items):
        """Supermarkt-spezifische Reihenfolge kann übergeben werden."""
        custom = [
            ("Getränke", ("beverages",)),
            ("Gemüse", ("vegetables",)),
            ("Sonstiges", ("other", "unknown_category_xyz", "fruit", "meat", "dairy",
                           "grains", "frozen", "canned", "spices")),
        ]
        groups = group_by_gang(export_items, gang_order=custom)
        assert [g["gang"] for g in groups][:2] == ["Getränke", "Gemüse"]

    def test_build_grocery_list_liefert_gang_reihenfolge(self):
        rid = uuid.uuid4()
        register_dummy_recipe(rid, [
            {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000301"),
             "quantity": 2.0, "unit": "Stück", "substitution_note": None},
            {"ingredient_id": uuid.UUID("00000000-0000-0000-0000-000000000302"),
             "quantity": 1.0, "unit": "Stück", "substitution_note": None},
        ])
        lookup = {
            uuid.UUID("00000000-0000-0000-0000-000000000301"): {"name": "Hackfleisch", "category": "meat"},
            uuid.UUID("00000000-0000-0000-0000-000000000302"): {"name": "Zucchini", "category": "vegetables"},
        }
        result = build_grocery_list({"meal_slots": [
            {"recipe_id": rid, "meal_type": "dinner", "servings_multiplier": 1.0, "is_repeat": False},
        ]}, lookup)
        assert [i["name"] for i in result["items"]] == ["Zucchini", "Hackfleisch"]
        assert list(result["grouped"].keys())[0] == "vegetables"
        assert result["gangs"][0]["gang"] == "Gemüse"


# ─── 2. CSV-Export ────────────────────────────────────────────────────────

class TestCsvExport:
    def test_csv_kopf_und_semikolon(self, export_items):
        rows = build_export_rows(export_items)
        csv_text = build_export_csv(rows)
        lines = csv_text.split("\r\n")
        assert lines[0] == "Menge;Einheit;Zutat;Gang"
        assert "3;Stück;Karotten;Gemüse" in csv_text
        assert "2,5" not in csv_text  # Äpfel sind 1,5 kg
        assert "1,5;kg;Äpfel;Obst" in csv_text

    def test_csv_zeilen_in_gang_reihenfolge(self, export_items):
        csv_text = build_export_csv(build_export_rows(export_items))
        positions = [csv_text.index(n) for n in ("Karotten", "Äpfel", "Hähnchenbrust", "Batterien")]
        assert positions == sorted(positions)

    def test_csv_quotet_semikolon_im_namen(self):
        rows = build_export_rows([_item("Käse; gerieben", "dairy", 100.0, "g")])
        csv_text = build_export_csv(rows)
        assert '"Käse; gerieben"' in csv_text

    def test_export_zeilen_formatieren_mengen(self):
        rows = build_export_rows([
            _item("Milch", "dairy", 1.0, "l"),
            _item("Butter", "dairy", 2.5, "Stück"),
        ])
        by_name = {r["name"]: r["quantity"] for r in rows}
        assert by_name["Milch"] == "1"
        assert by_name["Butter"] == "2,5"


# ─── 3. TXT-Export ────────────────────────────────────────────────────────

class TestTxtExport:
    def test_txt_hat_gang_ueberschriften(self, export_items):
        txt = build_export_txt(build_export_rows(export_items), week_number=12, supermarket="Rewe")
        assert txt.startswith("Einkaufsliste – Kalenderwoche 12")
        assert "Supermarkt: Rewe" in txt
        assert "== Gemüse ==" in txt
        assert "== Fleisch/Fisch ==" in txt
        assert "== Sonstiges ==" in txt

    def test_txt_zeilen_sind_lesbar(self, export_items):
        txt = build_export_txt(build_export_rows(export_items), week_number=12)
        assert "[ ] 3 Stück Karotten" in txt
        assert "[ ] 2 Stück Hähnchenbrust" in txt

    def test_txt_enthaelt_hinweis(self):
        txt = build_export_txt(
            build_export_rows([_item("Sahne", "dairy", 200.0, "ml", notes="Hafermilch")]),
        )
        assert "Hinweis: Hafermilch" in txt


# ─── 4. Export-Route: IDOR / 404 / Header ─────────────────────────────────

class _FakeListRepo:
    def __init__(self, gl):
        self._gl = gl

    async def get_with_items(self, _list_id):
        return self._gl


class _FakeItemRepo:
    def __init__(self, items):
        self._items = items

    async def get_by_list(self, _list_id):
        return self._items


def _install_route_fakes(monkeypatch, gl, items, household_id):
    """Patcht Repos + Ownership, damit die Route ohne DB testbar ist."""
    from app.routes import family
    from app.core import ownership

    monkeypatch.setattr(family, "GroceryListRepository", lambda db: _FakeListRepo(gl))
    monkeypatch.setattr(family, "GroceryItemRepository", lambda db: _FakeItemRepo(items))

    async def _households(db, user_id):
        return [SimpleNamespace(id=household_id, dietary_profile={"preferred_supermarket": "Rewe"})]

    monkeypatch.setattr(ownership, "get_user_households", _households)
    monkeypatch.setattr(family, "get_user_households", _households)
    return family


@pytest.mark.asyncio
async def test_export_fremde_liste_ist_404(monkeypatch):
    """IDOR: Liste eines fremden Haushalts → 404, kein Leak."""
    gl = SimpleNamespace(id=uuid.uuid4(), household_id=uuid.uuid4(), week_number=12)
    family = _install_route_fakes(monkeypatch, gl, [], household_id=uuid.uuid4())

    with pytest.raises(HTTPException) as exc:
        await family.export_grocery_list(gl.id, "csv", "user-1", None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_export_nicht_existierende_liste_ist_404(monkeypatch):
    family = _install_route_fakes(monkeypatch, None, [], household_id=uuid.uuid4())

    with pytest.raises(HTTPException) as exc:
        await family.export_grocery_list(uuid.uuid4(), "csv", "user-1", None)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_export_csv_route_liefert_bom_und_disposition(monkeypatch):
    hid = uuid.uuid4()
    gl = SimpleNamespace(id=uuid.uuid4(), household_id=hid, week_number=12)
    items = [_item("Karotten", "vegetables", 3.0, "Stück"), _item("Sahne", "dairy", 200.0, "ml")]
    family = _install_route_fakes(monkeypatch, gl, items, hid)

    response = await family.export_grocery_list(gl.id, "csv", "user-1", None)

    assert response.body.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    body = response.body.decode("utf-8-sig")
    assert "Menge;Einheit;Zutat;Gang" in body
    assert "3;Stück;Karotten;Gemüse" in body
    disposition = response.headers["content-disposition"]
    assert disposition.startswith('attachment; filename="einkaufsliste_kw12_')
    assert disposition.endswith('.csv"')
    assert "text/csv" in response.media_type


@pytest.mark.asyncio
async def test_export_txt_route_hat_gang_ueberschriften(monkeypatch):
    hid = uuid.uuid4()
    gl = SimpleNamespace(id=uuid.uuid4(), household_id=hid, week_number=12)
    items = [_item("Karotten", "vegetables", 3.0, "Stück")]
    family = _install_route_fakes(monkeypatch, gl, items, hid)

    response = await family.export_grocery_list(gl.id, "txt", "user-1", None)

    body = response.body.decode("utf-8")
    assert "== Gemüse ==" in body
    assert "[ ] 3 Stück Karotten" in body
    assert "text/plain" in response.media_type
    assert response.headers["content-disposition"].endswith('.txt"')
