"""Tests für die Allergen-Normalisierung im Plan-Generator.

Regression: „nüsse" (Nutzereingabe mit Umlaut) traf keinen Schlüssel in
ALLERGEN_MAP („nuesse"), dadurch wurde der Allergen-Filter komplett
übersprungen und ein Nuss-Allergiker bekam Mandel-Rezepte in den Plan.
"""
from types import SimpleNamespace
from uuid import uuid4

from app.services.plan_generator import (
    _build_allergen_set,
    _filter_by_allergens,
    _ingredient_matches,
    _norm_allergen,
)


class TestNormAllergen:
    def test_umlaut_wird_aufgeloest(self):
        assert _norm_allergen("Nüsse") == "nuese"
        assert _norm_allergen("  NÜSSE ") == "nuese"
        assert _norm_allergen("Schalenfrüchte") == "schalenfruechte"

    def test_ascii_bleibt(self):
        assert _norm_allergen("Gluten") == "gluten"


class TestBuildAllergenSet:
    def test_umlaut_variante_liefert_keywords(self):
        keywords = _build_allergen_set(["nüsse"])
        assert "mandeln" in keywords
        assert "walnuese" in keywords
        assert "haselnuese" in keywords

    def test_ascii_variante_identisch(self):
        assert _build_allergen_set(["nuesse"]) == _build_allergen_set(["Nüsse"])

    def test_synonym_nuss(self):
        assert "mandeln" in _build_allergen_set(["Nuss"])

    def test_unbekanntes_allergen_ignoriert(self):
        assert _build_allergen_set(["sonnenblumenkerne"]) == set()


class TestIngredientMatches:
    def test_teilstring_bei_langem_keyword(self):
        assert _ingredient_matches("mandeln (gemahlen)", {"mandeln"})

    def test_kurzes_keyword_nur_als_wort(self):
        assert not _ingredient_matches("eisbergsalat", {"ei"})
        assert _ingredient_matches("ei", {"ei"})

    def test_ohne_treffer(self):
        assert not _ingredient_matches("kartoffeln", {"mandeln", "walnues"})

    def test_erdnussoel_trifft_stamm(self):
        kw = _build_allergen_set(["nüsse"])
        assert _ingredient_matches(_norm_allergen("Erdnussöl (zum Frittieren)"), kw)

    def test_genuss_kein_fehlalarm(self):
        kw = _build_allergen_set(["nüsse"])
        assert not _ingredient_matches(_norm_allergen("Genussmittel"), kw)


class TestFilterByAllergens:
    def _setup(self, tags):
        rid, iid = uuid4(), uuid4()
        recipe = SimpleNamespace(id=rid, title="Hähnchen-Tajine", tags=tags)
        return recipe, rid, iid

    def test_tag_sortiert_umlaut_allergie_aus(self):
        recipe, rid, iid = self._setup(["orientalisch", "nuesse"])
        out = _filter_by_allergens(
            [recipe], ["nüsse"],
            {iid: "Mandeln"}, {iid: "Obst"}, {rid: [iid]},
        )
        assert out == []

    def test_zutat_sortiert_ungtaggt_aus(self):
        recipe, rid, iid = self._setup(["orientalisch"])
        out = _filter_by_allergens(
            [recipe], ["Nüsse"],
            {iid: "Haselnüsse"}, {iid: "Obst"}, {rid: [iid]},
        )
        assert out == []

    def test_ungefaehrliches_rezept_bleibt(self):
        recipe, rid, iid = self._setup(["orientalisch", "veggie"])
        out = _filter_by_allergens(
            [recipe], ["nüsse"],
            {iid: "Kichererbsen"}, {iid: "Gemüse"}, {rid: [iid]},
        )
        assert out == [recipe]
