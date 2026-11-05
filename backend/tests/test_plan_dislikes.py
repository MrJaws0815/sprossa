"""Task 35 / Task 18: Abneigungen (disliked_ingredients) im Plan-Generator.

Abneigungen sind eine WEICHE Regel: Rezepte mit Abneigung werden bevorzugt
gemieden, dürfen den Plan aber nicht blockieren. Bleibt nach dem Ausschluss
zu wenig Auswahl, wird der volle Pool zurückgegeben.
"""

import uuid

from app.services.plan_generator import _filter_by_dislikes, _parse_dislikes


class _Ing:
    def __init__(self, name):
        self.id = uuid.uuid4()
        self.name = name


class _Recipe:
    def __init__(self, title, ingredient_names):
        self.id = uuid.uuid4()
        self.title = title
        self._ings = [_Ing(n) for n in ingredient_names]

    @property
    def ingredients(self):
        return [type("RI", (), {"ingredient": i})() for i in self._ings]


def _index(recipes):
    id_to_name = {}
    rid_to_ings = {}
    for r in recipes:
        ids = []
        for ri in r.ingredients:
            ing = ri.ingredient
            id_to_name[ing.id] = ing.name
            ids.append(ing.id)
        rid_to_ings[r.id] = ids
    return id_to_name, rid_to_ings


# ── _parse_dislikes ────────────────────────────────────────────────────────

def test_parse_comma_separated_string():
    assert _parse_dislikes({"disliked_ingredients": "Pilze, Rosenkohl"}) == {"pilze", "rosenkohl"}


def test_parse_list_form():
    assert _parse_dislikes({"dislikes": ["Okra", "Leber"]}) == {"okra", "leber"}


def test_parse_newlines_and_semicolon_free():
    assert _parse_dislikes({"disliked_ingredients": "Pilze\nRosenkohl"}) == {"pilze", "rosenkohl"}


def test_parse_empty_and_missing():
    assert _parse_dislikes({}) == set()
    assert _parse_dislikes({"disliked_ingredients": ""}) == set()
    assert _parse_dislikes(None) == set()


def test_parse_lowercases_and_strips():
    assert _parse_dislikes({"disliked_ingredients": "  PILZE ,  rosenkohl "}) == {"pilze", "rosenkohl"}


# ── _filter_by_dislikes ────────────────────────────────────────────────────

def _pool(n_clean=30, n_hit=5):
    """Baut einen Pool: saubere Rezepte + Rezepte mit Abneigung."""
    recipes = [
        _Recipe(f"Sauber {i}", ["Kartoffeln", "Karotten"]) for i in range(n_clean)
    ]
    recipes += [
        _Recipe(f"Pilzpfanne {i}", ["Pilze", "Reis"]) for i in range(n_hit)
    ]
    return recipes


def test_no_dislikes_returns_pool_unchanged():
    recipes = _pool()
    id_to_name, rid_to_ings = _index(recipes)
    assert _filter_by_dislikes(recipes, set(), id_to_name, rid_to_ings) == recipes


def test_dislikes_remove_matching_recipes_when_pool_is_big_enough():
    recipes = _pool(n_clean=30, n_hit=5)
    id_to_name, rid_to_ings = _index(recipes)
    result = _filter_by_dislikes(recipes, {"pilze"}, id_to_name, rid_to_ings)
    assert len(result) == 30
    assert all("Pilz" not in r.title for r in result)


def test_dislikes_fall_back_when_pool_too_small():
    """Weiche Regel: bei zu kleinem Restpool bleibt der volle Pool erhalten."""
    recipes = _pool(n_clean=10, n_hit=5)  # nur 10 saubere < min_pool 20
    id_to_name, rid_to_ings = _index(recipes)
    result = _filter_by_dislikes(recipes, {"pilze"}, id_to_name, rid_to_ings)
    assert len(result) == len(recipes), "Fallback muss vollen Pool liefern"


def test_dislikes_match_is_case_insensitive():
    recipes = _pool(n_clean=30, n_hit=5)
    id_to_name, rid_to_ings = _index(recipes)
    result = _filter_by_dislikes(recipes, {"PILZE"}, id_to_name, rid_to_ings)
    assert len(result) == 30


def test_dislikes_ignore_unknown_ingredients():
    recipes = _pool(n_clean=30, n_hit=5)
    id_to_name, rid_to_ings = _index(recipes)
    result = _filter_by_dislikes(recipes, {"durian"}, id_to_name, rid_to_ings)
    assert len(result) == len(recipes)
