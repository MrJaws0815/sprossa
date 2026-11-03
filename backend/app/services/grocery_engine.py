"""Grocery-Engine: Aus Wochen-/Monatsplänen Einkaufslisten generieren.

Domain-Regeln (TDD-Anker):
1. Alle Zutaten über alle Slots eines Zeitraums werden summiert
2. CookOnce-EatTwice-Rezepte werden NUR einfach in die Summe eingerechnet
3. Zutaten werden nach Kategorie gruppiert (Gemüse, Fleisch, etc.)
4. Selbe Zutat (gleiche Einheit) wird aufsummiert
5. Optionale Zutaten werden gesondert markiert
6. Substitutionen werden angewandt falls konfiguriert
"""
import csv
import io
import re
from collections import defaultdict
from typing import Iterable, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    GroceryItem as GroceryItemModel,
    GroceryList as GroceryListModel,
    MealSlot,
    Recipe,
    RecipeIngredient,
    WeeklyPlan,
)
from app.repositories.grocery import GroceryItemRepository, GroceryListRepository
from app.repositories.ingredient import IngredientRepository
from app.repositories.recipe import RecipeRepository


# ─── Supermarkt-Gang-Reihenfolge (konfigurierbar) ─────────────────────────
# Reihenfolge, in der ein Supermarkt üblicherweise durchlaufen wird. Jeder
# Eintrag ist (Gang-Label, Kategorie-Slugs). Ein Supermarkt-spezifisches
# Profil kann diese Liste später ersetzen oder erweitern; alle Funktionen
# unten akzeptieren optional eine eigene `gang_order`.
#
# Werbeaussage "nach Supermarkt-Gängen gruppiert" hängt an dieser Konstante.
SUPERMARKET_GANG_ORDER: list[tuple[str, tuple[str, ...]]] = [
    # Slug-Listen enthalten sowohl die kanonischen Labels (nach Task 53) als
    # auch historische DE/EN-Varianten, damit alte Daten weiter sortieren.
    ("Gemüse", ("gemüse", "gemuese", "vegetables", "gemüse & kräuter", "kräuter", "algen")),
    ("Obst", ("obst", "fruit", "fruits", "beeren")),
    ("Fleisch/Fisch", (
        "fleisch", "meat", "geflügel", "wurst", "fleisch & fisch",
        "fisch", "fish", "meeresfrüchte", "fisch & meeresfrüchte", "seafood",
    )),
    ("Milchprodukte/Eier", (
        "milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs",
        "eier", "eggs", "käse",
    )),
    ("Backwaren", ("backwaren", "bread", "bakery", "backzutaten", "baking", "grains")),
    ("Tiefkühl", ("tiefkühl", "tiefkuehl", "frozen", "tk & fertigprodukte")),
    ("Getränke", ("getränke", "getraenke", "beverages", "drinks")),
    ("Vorrat/Konserven", (
        "vorrat", "vorrat & konserven", "konserven", "canned", "condiments",
        "pantry", "getreide", "reis & getreide", "nudeln", "hülsenfrüchte",
        "nüsse", "soßen & öle", "soßen & oele", "sauces", "oils",
    )),
    ("Gewürze", ("gewürze", "gewuerze", "spices", "gewürze & brühen", "brühen")),
    ("Sonstiges", ("other", "sonstiges", "misc", "küchenbedarf", "kuechenbedarf", "hilfsmittel", "tofu")),
]

GANG_ORDER: list[str] = [label for label, _ in SUPERMARKET_GANG_ORDER]

# ─── Supermarkt-spezifische Gang-Reihenfolgen (Task 82) ───────────────────
# Jede Kette hat ihre eigene, realistische Laufreihenfolge. Die Gang-Labels
# bleiben identisch, nur die Reihenfolge variiert. "anderer" fällt auf Rewe
# zurück (siehe get_gang_order).
_GANG_SLUGS: dict[str, tuple[str, ...]] = {
    label: slugs for label, slugs in SUPERMARKET_GANG_ORDER
}

SUPERMARKET_GANG_ORDERS: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "rewe": list(SUPERMARKET_GANG_ORDER),
    "aldi": [
        ("Backwaren", _GANG_SLUGS["Backwaren"]),
        ("Gemüse", _GANG_SLUGS["Gemüse"]),
        ("Obst", _GANG_SLUGS["Obst"]),
        ("Milchprodukte/Eier", _GANG_SLUGS["Milchprodukte/Eier"]),
        ("Fleisch/Fisch", _GANG_SLUGS["Fleisch/Fisch"]),
        ("Tiefkühl", _GANG_SLUGS["Tiefkühl"]),
        ("Vorrat/Konserven", _GANG_SLUGS["Vorrat/Konserven"]),
        ("Getränke", _GANG_SLUGS["Getränke"]),
        ("Gewürze", _GANG_SLUGS["Gewürze"]),
        ("Sonstiges", _GANG_SLUGS["Sonstiges"]),
    ],
    "edeka": [
        ("Obst", _GANG_SLUGS["Obst"]),
        ("Gemüse", _GANG_SLUGS["Gemüse"]),
        ("Fleisch/Fisch", _GANG_SLUGS["Fleisch/Fisch"]),
        ("Milchprodukte/Eier", _GANG_SLUGS["Milchprodukte/Eier"]),
        ("Backwaren", _GANG_SLUGS["Backwaren"]),
        ("Tiefkühl", _GANG_SLUGS["Tiefkühl"]),
        ("Getränke", _GANG_SLUGS["Getränke"]),
        ("Vorrat/Konserven", _GANG_SLUGS["Vorrat/Konserven"]),
        ("Gewürze", _GANG_SLUGS["Gewürze"]),
        ("Sonstiges", _GANG_SLUGS["Sonstiges"]),
    ],
    "lidl": [
        ("Backwaren", _GANG_SLUGS["Backwaren"]),
        ("Obst", _GANG_SLUGS["Obst"]),
        ("Gemüse", _GANG_SLUGS["Gemüse"]),
        ("Fleisch/Fisch", _GANG_SLUGS["Fleisch/Fisch"]),
        ("Milchprodukte/Eier", _GANG_SLUGS["Milchprodukte/Eier"]),
        ("Tiefkühl", _GANG_SLUGS["Tiefkühl"]),
        ("Vorrat/Konserven", _GANG_SLUGS["Vorrat/Konserven"]),
        ("Getränke", _GANG_SLUGS["Getränke"]),
        ("Gewürze", _GANG_SLUGS["Gewürze"]),
        ("Sonstiges", _GANG_SLUGS["Sonstiges"]),
    ],
}
# "anderer" ist ein Alias für Rewe (Fallback).
SUPERMARKET_GANG_ORDERS["anderer"] = SUPERMARKET_GANG_ORDERS["rewe"]


def get_gang_order(
    supermarket: Optional[str],
) -> list[tuple[str, tuple[str, ...]]]:
    """Liefert die Gang-Reihenfolge zur Supermarkt-Kette (Fallback: Rewe).

    Case-insensitive; unbekannte/leere Werte fallen auf Rewe zurück.
    """
    key = str(supermarket or "").strip().lower()
    return SUPERMARKET_GANG_ORDERS.get(key, SUPERMARKET_GANG_ORDERS["rewe"])


# ─── Zutaten-Gruppierungsregeln (Task 81) ────────────────────────────────
# Rezepte behalten ihre spezifische Zutat; nur die EINKAUFSLISTE gruppiert
# Varianten (z. B. Kartoffeln (festkochend) + Kartoffeln (mehligkochend)).
# Regeln werden auf den normalisierten Namen (ohne Klammerzusätze, lowercase)
# angewendet. Reihenfolge ist wichtig: spezifische Regeln VOR generischen.
INGREDIENT_GROUP_RULES: list[tuple[str, str, Optional[tuple[str, ...]]]] = [
    # (Regex, Gruppenname, optionale erlaubte Kategorien)
    (r"^s[uü](?:ß|ss)?kartoffeln?$", "Süsskartoffeln", ("gemüse", "gemuese", "vegetables")),
    (r"^(?:junge\s+)?kartoffeln?$", "Kartoffeln", ("gemüse", "gemuese", "vegetables")),
    (r"(?:cherry)?tomaten?$", "Tomaten", ("gemüse", "gemuese", "vegetables")),
    (r"^zwiebeln?$", "Zwiebeln", ("gemüse", "gemuese", "vegetables")),
    (r"^(?:äpfel|aepfel|apfel)$", "Aepfel", ("obst", "fruit", "fruits")),
    (r"^(?:karotten|m[oö]hren|mohrr(?:ü|ue)ben)$", "Karotten", ("gemüse", "gemuese", "vegetables")),
    (r"paprika$", "Paprika", ("gemüse", "gemuese", "vegetables")),
    (r"^(?:käse|kaese)$", "Kaese", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs", "käse")),
    (r"^mehl$", "Mehl", ("backwaren", "bread", "bakery", "backzutaten", "baking", "grains")),
    (r"^reis$", "Reis", ("vorrat", "vorrat & konserven", "konserven", "pantry", "getreide", "reis & getreide")),
    (r"^nudeln?$", "Nudeln", ("vorrat", "vorrat & konserven", "konserven", "pantry", "nudeln")),
    (r"^butter$", "Butter", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs")),
    (r"^milch$", "Milch", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs")),
    (r"^sahne$", "Sahne", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs")),
    (r"^joghurt$", "Joghurt", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs")),
    (r"^quark$", "Quark", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs")),
    (r"^eier?$", "Eier", ("milchprodukte", "milchprodukte & eier", "dairy", "dairy & eggs", "eier", "eggs")),
]

_GROUP_RULES_COMPILED = [
    (re.compile(pattern, re.IGNORECASE), group, categories)
    for pattern, group, categories in INGREDIENT_GROUP_RULES
]

_PAREN_RE = re.compile(r"\s*\([^)]*\)")


def _normalize_ingredient_name(name: str) -> str:
    """Entfernt Klammerzusätze, normalisiert Whitespace und lowercase."""
    value = _PAREN_RE.sub(" ", str(name or ""))
    return " ".join(value.split()).strip().lower()


def _group_key(name: str, category: Optional[str] = None) -> str:
    """Liefert den Gruppenschlüssel für eine Zutat.

    Varianten (z. B. "Kartoffeln (festkochend)") werden auf ihren Grundnamen
    ("Kartoffeln") abgebildet. Kategorien schützen vor Fehlgruppierungen
    (z. B. Kartoffelklöße aus der Vorrat-Abteilung bleiben eigenständig).
    """
    normalized = _normalize_ingredient_name(name)
    if not normalized:
        return ""
    cat = str(category or "").strip().lower()
    for regex, group, allowed in _GROUP_RULES_COMPILED:
        if allowed is not None and cat and cat not in allowed:
            continue
        if regex.match(normalized):
            return group
    # Kein Treffer: Originalname (ohne Klammer-/Whitespace-Bereinigung) erhalten,
    # damit Schreibweise und Unterscheidbarkeit nicht verloren gehen.
    return " ".join(str(name or "").split()).strip()


def _variant_suffix(name: str, group: str) -> str:
    """Liefert den Varianten-Zusatz einer Zutat relativ zum Gruppennamen.

    Beispiele:
      "Kartoffeln (festkochend)", "Kartoffeln" -> "festkochend"
      "Kartoffeln", "Kartoffeln"              -> ""
      "Junge Kartoffeln", "Kartoffeln"        -> "junge"
    """
    raw = str(name or "").strip()
    lowered = raw.lower()
    group_lower = group.lower()
    # Klammerinhalt extrahieren
    match = re.search(r"\(([^)]*)\)", raw)
    if match:
        return match.group(1).strip().lower()
    # Kein Klammerzusatz: Differenz zum Gruppennamen
    if lowered == group_lower:
        return ""
    if lowered.endswith(group_lower):
        prefix = raw[: -len(group)].strip(" -,")
        return prefix.lower()
    if lowered.startswith(group_lower):
        suffix = raw[len(group):].strip(" -,")
        return suffix.lower()
    return lowered


def _gang_table(
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
) -> tuple[dict[str, str], dict[str, int], str]:
    """Baut (Slug→Gang, Gang→Index, Fallback-Gang) für eine Reihenfolge."""
    order = gang_order or SUPERMARKET_GANG_ORDER
    by_slug: dict[str, str] = {}
    index: dict[str, int] = {}
    for i, (label, slugs) in enumerate(order):
        index[label] = i
        for slug in slugs:
            by_slug[slug.lower()] = label
    fallback = order[-1][0]
    return by_slug, index, fallback


def gang_for_category(
    category: Optional[str],
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
) -> str:
    """Mappt eine Zutaten-Kategorie auf das Gang-Label.

    Unbekannte/leere Kategorien landen im letzten Gang ("Sonstiges").
    """
    by_slug, _, fallback = _gang_table(gang_order)
    if not category:
        return fallback
    return by_slug.get(str(category).strip().lower(), fallback)


def gang_sort_index(
    category: Optional[str],
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
) -> int:
    """Sortierschlüssel (Gang-Index) für eine Kategorie; unbekannt → Ende."""
    by_slug, index, fallback = _gang_table(gang_order)
    label = by_slug.get(str(category).strip().lower(), fallback) if category else fallback
    return index.get(label, len(index) - 1)


def _item_category(item, category_key: str = "category") -> Optional[str]:
    """Liest die Kategorie aus dict oder ORM-Objekt.

    Fallback für GroceryItem: category_override, dann ingredient.category.
    """
    if isinstance(item, dict):
        return item.get(category_key)
    value = getattr(item, category_key, None)
    if not value:
        value = getattr(item, "category_override", None)
    if not value:
        ingredient = getattr(item, "ingredient", None)
        value = getattr(ingredient, "category", None) if ingredient is not None else None
    return value


def _item_name(item, name_key: str = "name") -> str:
    if isinstance(item, dict):
        return str(item.get(name_key) or "")
    return str(getattr(item, name_key, "") or "")


def _resolve_gang_order(
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
    supermarket: Optional[str] = None,
) -> Sequence[tuple[str, Sequence[str]]]:
    """Priorität: explizite gang_order > Supermarkt-Profil > Rewe-Default."""
    if gang_order:
        return gang_order
    return get_gang_order(supermarket)


def sort_by_gang(
    items: Iterable,
    category_key: str = "category",
    name_key: str = "name",
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
    supermarket: Optional[str] = None,
):
    """Sortiert Items stabil nach Gang-Reihenfolge, innerhalb eines Gangs nach Name."""
    order = _resolve_gang_order(gang_order, supermarket)
    return sorted(
        items,
        key=lambda it: (
            gang_sort_index(_item_category(it, category_key), order),
            _item_name(it, name_key).lower(),
        ),
    )


def group_by_gang(
    items: Iterable,
    category_key: str = "category",
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
    supermarket: Optional[str] = None,
) -> list[dict]:
    """Gruppiert Items nach Gang – leere Gänge werden ausgelassen.

    Rückgabe: [{"gang": "Gemüse", "items": [...]}, ...] in Supermarkt-Reihenfolge.
    """
    order = _resolve_gang_order(gang_order, supermarket)
    buckets: dict[str, list] = {label: [] for label, _ in order}
    for item in items:
        buckets[gang_for_category(_item_category(item, category_key), order)].append(item)
    return [{"gang": label, "items": buckets[label]} for label, _ in order if buckets[label]]


def _format_quantity(value: float) -> str:
    """3.0 → '3', 2.5 → '2,5' (deutsche Dezimalschreibweise)."""
    number = round(float(value), 2)
    if number == int(number):
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def build_export_rows(
    items: Iterable,
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
    supermarket: Optional[str] = None,
) -> list[dict]:
    """Normalisiert ORM-Items/dicts zu flachen Export-Zeilen in Gang-Reihenfolge."""
    order = _resolve_gang_order(gang_order, supermarket)
    rows: list[dict] = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name") or item.get("ingredient_name") or "Zutat"
            category = item.get("category")
            quantity = item.get("total_quantity", item.get("quantity_total", 0))
            unit = item.get("unit", "")
            notes = item.get("notes")
        else:
            ingredient = getattr(item, "ingredient", None)
            raw_name = getattr(ingredient, "name", None) or str(getattr(item, "ingredient_id", "Zutat"))
            category = getattr(item, "category_override", None)
            if not category and ingredient is not None:
                category = getattr(ingredient, "category", None)
            quantity = getattr(item, "quantity_total", 0)
            unit = getattr(item, "unit", "")
            raw_notes = getattr(item, "notes", None)
            # Task 81: Varianten-Marker aus notes in den Anzeigenamen überführen.
            # Nur bei tatsächlich gruppierten Posten (Marker vorhanden) wird der
            # Name umgeschrieben; rohe Items behalten ihren Originalnamen.
            if raw_notes and "varianten:" in str(raw_notes).lower():
                name = grocery_item_display_name(raw_name, raw_notes, category)
            else:
                name = str(raw_name)
            notes = _clean_item_notes(raw_notes)
        rows.append({
            "quantity": _format_quantity(quantity),
            "unit": str(unit or ""),
            "name": str(name),
            "category": category or "other",
            "gang": gang_for_category(category, order),
            "notes": notes,
        })
    return sorted(
        rows,
        key=lambda r: (gang_sort_index(r["category"], order), r["name"].lower()),
    )


def build_export_csv(
    rows: Sequence[dict],
    supermarket: Optional[str] = None,
    gang_order: Optional[Sequence[tuple[str, Sequence[str]]]] = None,
) -> str:
    """CSV mit Semikolon-Trennung und CRLF (deutsche Excel-Kompatibilität).

    Der UTF-8-BOM wird vom Route-Layer vorangestellt, damit Excel die Datei
    als UTF-8 erkennt; hier bleibt der Text BOM-frei (leichter testbar).
    Die Zeilen werden nach der Supermarkt-spezifischen Gang-Reihenfolge sortiert.
    """
    order = _resolve_gang_order(gang_order, supermarket)
    ordered_rows = sorted(
        rows,
        key=lambda r: (gang_sort_index(r.get("category"), order), str(r.get("name", "")).lower()),
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Menge", "Einheit", "Zutat", "Gang"])
    for row in ordered_rows:
        writer.writerow([row["quantity"], row["unit"], row["name"], row["gang"]])
    return buffer.getvalue()


def build_export_txt(
    rows: Sequence[dict],
    week_number: Optional[int] = None,
    supermarket: Optional[str] = None,
) -> str:
    """Druckbare Textliste mit Gang-Überschriften."""
    title = "Einkaufsliste"
    if week_number is not None:
        title += f" – Kalenderwoche {week_number}"
    else:
        title += " – Monatsliste"
    lines = [title]
    if supermarket:
        lines.append(f"Supermarkt: {supermarket}")
    lines.append("")
    for group in group_by_gang(rows, supermarket=supermarket):
        lines.append(f"== {group['gang']} ==")
        for row in group["items"]:
            quantity = f"{row['quantity']} {row['unit']}".strip()
            line = f"[ ] {quantity} {row['name']}".replace("  ", " ").strip()
            if row.get("notes"):
                line += f"  – Hinweis: {row['notes']}"
            lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ─── Legacy: In-Memory Dummy-Cache für bestehende Tests ──────────────────

_RECIPE_CACHE: dict[UUID, list[dict]] = {}

def register_dummy_recipe(recipe_id: UUID, ingredients: list[dict]):
    """Registriert ein Rezept mit Zutaten für Tests/Prototypen."""
    _RECIPE_CACHE[recipe_id] = ingredients

def _get_recipe_ingredients(recipe_id: UUID) -> list[dict]:
    """Holt Zutaten für ein Rezept (Dummy-Cache)."""
    return _RECIPE_CACHE.get(recipe_id, [])


def build_grocery_list(
    weekly_plan: dict,
    ingredients_lookup: dict[UUID, dict],
    apply_substitutions: Optional[dict[str, str]] = None,
    supermarket: Optional[str] = None,
) -> dict:
    """Erzeugt eine Einkaufsliste aus einem Wochenplan (Legacy, In-Memory).

    weekly_plan: {
        "meal_slots": [ { "recipe_id": UUID, "meal_type": str, "servings_multiplier": float, "is_repeat": bool }, ... ]
    }
    ingredients_lookup: { ingredient_id: { "name": str, "category": str } }

    Rückgabe: {
        "items": [ { "ingredient_id": UUID, "name": str, "category": str, "total_quantity": float, "unit": str }, ... ],
        "grouped": { "vegetables": [...], "meat": [...], ... }
    }
    """
    # Task 81: Varianten derselben Zutatengruppe werden NUR in der Einkaufsliste
    # zusammengefasst – Rezept-Zutaten (recipe_ingredients) bleiben unverändert.
    # Aggregationsschlüssel ist (group_key, unit): Mengen werden nur bei
    # identischer Einheit summiert.
    aggregated: dict[tuple[str, str], GroceryItemBuilder] = {}
    group_variants: dict[str, set[str]] = defaultdict(set)

    for slot in weekly_plan.get("meal_slots", []):
        if slot.get("is_repeat", False):
            continue  # CookOnce-EatTwice: nur einmal einkaufen

        recipe_id = slot["recipe_id"]
        servings_mult = slot.get("servings_multiplier", 1.0)

        recipe_ingredients = _get_recipe_ingredients(recipe_id)

        for ri in recipe_ingredients:
            iid = ri["ingredient_id"]
            info = ingredients_lookup.get(iid, {"name": "?", "category": "other"})
            name = info["name"]
            category = info["category"]
            gkey = _group_key(name, category)
            unit = str(ri["unit"] or "")
            key = (gkey, unit)
            if key not in aggregated:
                base_name = name if gkey == _normalize_ingredient_name(name) else gkey
                aggregated[key] = GroceryItemBuilder(iid, gkey, base_name, category)
            builder = aggregated[key]
            qty = ri["quantity"] * servings_mult
            builder.add(qty, unit, ri.get("substitution_note"))
            suffix = _variant_suffix(name, gkey)
            if suffix:
                group_variants[gkey].add(suffix)

    # In Supermarkt-Gang-Reihenfolge sortieren (Werbeaussage "nach Gängen gruppiert")
    order = get_gang_order(supermarket)
    items = sort_by_gang(
        (
            {
                "ingredient_id": str(builder.ingredient_id),
                "name": builder.display_name(group_variants[builder.group_key]),
                "category": builder.category,
                "total_quantity": round(builder.total_quantity, 2),
                "unit": builder.unit,
                "notes": builder.notes,
            }
            for builder in aggregated.values()
        ),
        gang_order=order,
    )

    # Gruppieren – Schlüssel in Gang-Reihenfolge (dict bewahrt Insertion-Order)
    grouped: dict[str, list] = defaultdict(list)
    for item in items:
        grouped[item["category"]].append(item)
    ordered_grouped = {
        slug: grouped[slug]
        for label, slugs in order
        for slug in slugs
        if slug in grouped
    }
    # Unbekannte Kategorien ans Ende (kein Verlust, nur Reihenfolge)
    for slug, entries in grouped.items():
        ordered_grouped.setdefault(slug, entries)

    return {
        "items": items,
        "grouped": ordered_grouped,
        "gangs": group_by_gang(items, gang_order=order),
    }


def grocery_item_display_name(
    ingredient_name: str,
    notes: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """Bildet den Anzeigenamen für einen Einkaufsposten inkl. Varianten-Hinweis.

    In `notes` abgelegte Varianten (Format "Varianten: a, b") werden an den
    Gruppennamen angehängt: "Kartoffeln (festkochend, mehligkochend)".
    """
    base = _group_key(ingredient_name, category) or str(ingredient_name or "").strip()
    match = re.search(r"(?:^|;\s*)Varianten:\s*([^;]+)", str(notes or ""), re.IGNORECASE)
    if match:
        variants = match.group(1).strip()
        # Kein doppelter Klammerzusatz: wenn der Basisname bereits einen
        # Klammer-Hinweis enthält (z. B. "Hefe (frisch)"), nicht erneut anhängen.
        if variants and "(" not in base:
            return f"{base} ({variants})"
    return base


def _clean_item_notes(notes: Optional[str]) -> Optional[str]:
    """Entfernt den internen Varianten-Marker aus den Anzeige-Hinweisen."""
    if not notes:
        return None
    parts = [p.strip() for p in str(notes).split("; ") if p.strip()]
    remaining = [p for p in parts if not p.lower().startswith("varianten:")]
    return "; ".join(remaining) if remaining else None


class GroceryItemBuilder:
    """Baut einen Einkaufslisten-Posten aus einer Zutaten-Gruppe + Einheit.

    Aggregiert werden Varianten derselben Gruppe (z. B. Kartoffeln fest- und
    mehligkochend) – aber nur bei identischer Einheit. Die Rezept-Zutaten
    selbst bleiben unverändert.
    """
    def __init__(self, ingredient_id: UUID, group_key: str, name: str, category: str):
        self.ingredient_id = ingredient_id
        self.group_key = group_key
        self.name = name
        self.category = category
        self.total_quantity = 0.0
        self.unit = ""
        self.notes: list[str] = []
        self.variants: set[str] = set()

    def add(self, quantity: float, unit: str, note: Optional[str] = None):
        """Addiert eine Menge; der Builder ist bereits nach Einheit getrennt."""
        self.unit = unit or self.unit
        self.total_quantity += quantity
        if note:
            self.notes.append(note)

    def display_name(self, group_variants: Optional[set[str]] = None) -> str:
        variants = sorted(v for v in (group_variants or self.variants) if v)
        if variants:
            return f"{self.name} ({', '.join(variants)})"
        return self.name


async def generate_and_persist_grocery_list(
    weekly_plan: WeeklyPlan,
    db: AsyncSession,
    household_id: UUID,
    monthly_plan_id: Optional[UUID] = None,
    week_number: Optional[int] = None,
    supermarket: Optional[str] = None,
    segment_label: Optional[str] = None,
) -> GroceryListModel:
    """Generiert eine Einkaufsliste aus einem WeeklyPlan und persistiert sie.

    Lädt Rezept-Zutaten aus der DB, aggregiert sie (CookOnce-Respekt),
    und schreibt GroceryList + GroceryItems in die Datenbank.

    Task 81: Varianten derselben Zutatengruppe werden NUR hier (Einkaufsliste)
    zusammengefasst; RecipeIngredients bleiben unverändert. Task 82: Sortierung
    nach supermarkt-spezifischer Gang-Reihenfolge. Task 85: segment_label wird
    (falls vorhanden) als Hinweis an die Liste gehängt.
    """
    # Lade alle Recipe-IDs aus den MealSlots
    meal_slots = weekly_plan.meal_slots
    recipe_ids = list({s.recipe_id for s in meal_slots})

    # Rezepte mit Zutaten laden
    recipe_repo = RecipeRepository(db)
    recipes_with_ingredients = {}
    for rid in recipe_ids:
        recipe = await recipe_repo.get_with_ingredients(rid)
        if recipe:
            recipes_with_ingredients[rid] = recipe

    # Ingredient-Lookup (Name, Kategorie)
    ing_repo = IngredientRepository(db)
    all_ingredients = await ing_repo.get_all()
    ingredient_lookup = {i.id: {"name": i.name, "category": i.category} for i in all_ingredients}

    # Aggregieren – Task 81: nach group_key statt ingredient_id gruppieren,
    # aber nur bei identischer Einheit (unit-aware). Rezept-Zutaten bleiben
    # unverändert; nur diese Einkaufslisten-Aggregation fasst Varianten zusammen.
    aggregated: dict[tuple[str, str], GroceryItemBuilder] = {}
    group_variants: dict[str, set[str]] = defaultdict(set)
    used_ingredient_ids: set[UUID] = set()

    # Basis-Zutaten (Name == Gruppenname) für stabile Anzeigenamen finden.
    name_to_ingredient_id: dict[str, UUID] = {}
    for iid, info in ingredient_lookup.items():
        key = str(info.get("name", "")).strip().lower()
        name_to_ingredient_id.setdefault(key, iid)

    for slot in meal_slots:
        if slot.is_repeat:
            continue  # CookOnce-EatTwice: nur einmal einkaufen

        recipe = recipes_with_ingredients.get(slot.recipe_id)
        if not recipe:
            continue

        servings_mult = slot.servings_multiplier

        for ri in recipe.ingredients:
            iid = ri.ingredient_id
            info = ingredient_lookup.get(iid, {"name": "?", "category": "other"})
            name = info["name"]
            category = info["category"]
            gkey = _group_key(name, category)
            unit = str(ri.unit or "")
            key = (gkey, unit)
            if key not in aggregated:
                base_name = name if gkey == _normalize_ingredient_name(name) else gkey
                base_id = name_to_ingredient_id.get(gkey.strip().lower())
                rep_id = base_id if base_id is not None else iid
                aggregated[key] = GroceryItemBuilder(rep_id, gkey, base_name, category)
            builder = aggregated[key]
            qty = ri.quantity * servings_mult
            builder.add(qty, unit, ri.substitution_note)
            suffix = _variant_suffix(name, gkey)
            if suffix:
                group_variants[gkey].add(suffix)

    # GroceryList anlegen – segment_label wird (falls vorhanden) an die
    # generierten_at-Liste als Hinweis angehängt; das DB-Modell hat kein
    # eigenes Label-Feld. Der Aufrufer (family.py/API) leitet das Label aus
    # week_number + Segment-Index ab (Fallback).
    gl_repo = GroceryListRepository(db)
    grocery_list = await gl_repo.create(
        household_id=household_id,
        monthly_plan_id=monthly_plan_id,
        week_number=week_number,
        is_master_list=(week_number is None),
    )
    if segment_label:
        # Kein DB-Feld: Label am ORM-Objekt für den Aufrufer merken (nicht persistiert).
        try:
            grocery_list.segment_label = segment_label
        except Exception:
            pass

    # GroceryItems anlegen – direkt in Supermarkt-Gang-Reihenfolge, damit
    # API-Antworten ohne zusätzliche Sortierung gangweise gelesen werden.
    gi_repo = GroceryItemRepository(db)
    order = get_gang_order(supermarket)
    ordered_builders = sorted(
        aggregated.values(),
        key=lambda b: (
            gang_sort_index(b.category, order),
            b.display_name(group_variants[b.group_key]).lower(),
        ),
    )
    for builder in ordered_builders:
        display = builder.display_name(group_variants[builder.group_key])
        notes_parts: list[str] = []
        # Varianten nur dann als Hinweis ablegen, wenn es echte Zusätze gibt.
        variants = sorted(v for v in group_variants.get(builder.group_key, set()) if v)
        if variants and display != builder.name:
            notes_parts.append(f"Varianten: {', '.join(variants)}")
        if builder.notes:
            notes_parts.extend(str(n) for n in builder.notes if n)
        ingredient_id = builder.ingredient_id
        # Doppelte ingredient_id innerhalb derselben Liste vermeiden
        # (z. B. gleiche Gruppe in verschiedenen Einheiten).
        if ingredient_id in used_ingredient_ids:
            # Alternative Varianten-ID suchen (nicht bereits verwendet).
            alt = next(
                (iid for iid in ingredient_lookup if iid not in used_ingredient_ids
                 and _group_key(ingredient_lookup[iid]["name"], ingredient_lookup[iid]["category"]) == builder.group_key),
                None,
            )
            if alt is not None:
                ingredient_id = alt
        used_ingredient_ids.add(ingredient_id)
        await gi_repo.create(
            grocery_list_id=grocery_list.id,
            ingredient_id=ingredient_id,
            quantity_total=round(builder.total_quantity, 2),
            unit=builder.unit,
            category_override=builder.category,
            notes="; ".join(notes_parts) if notes_parts else None,
        )

    await db.refresh(grocery_list)
    return grocery_list