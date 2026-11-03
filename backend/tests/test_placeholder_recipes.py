"""Tests für den Platzhalter-/Demo-Rezept-Filter im Plan-Generator.

Deckt die Blacklist ab, die verhindert, dass Demo-Rezepte („Testrezept 1–6“,
„Rezept A/B/C“, „Einziges Rezept“) in Pläne echter Nutzer gelangen.
"""
import pytest

from app.services.plan_generator import (
    PLACEHOLDER_TITLE_PATTERNS,
    _is_placeholder_title,
)


class TestPlaceholderTitlePatterns:
    def test_patterns_konstante_enthaelt_alle_begriffe(self):
        assert "testrezept" in PLACEHOLDER_TITLE_PATTERNS
        assert "rezept a" in PLACEHOLDER_TITLE_PATTERNS
        assert "rezept b" in PLACEHOLDER_TITLE_PATTERNS
        assert "rezept c" in PLACEHOLDER_TITLE_PATTERNS
        assert "einziges rezept" in PLACEHOLDER_TITLE_PATTERNS

    @pytest.mark.parametrize(
        "title",
        [
            "Testrezept 1",
            "Testrezept 6",
            "TESTREZEPT 3",
            "testrezept",
            "Rezept A",
            "Rezept B",
            "Rezept C",
            "rezept a",
            "Rezept A (Test)",
            "Einziges Rezept",
            "einziges rezept",
            "Mein Einziges Rezept für heute",
        ],
    )
    def test_platzhalter_werden_erkannt(self, title):
        assert _is_placeholder_title(title) is True

    @pytest.mark.parametrize(
        "title",
        [
            "Spaghetti Bolognese",
            "Rezeptsammlung Herbst",  # beginnt mit "Rezept", aber nicht A/B/C
            "Rezept Apfelkuchen",     # "rezept a" als Präfix? -> bewusst NICHT
            "Kartoffelsuppe",
            "Reis mit Gemüse",
            "",
            None,
        ],
    )
    def test_echte_rezepte_bleiben(self, title):
        assert _is_placeholder_title(title) is False

    def test_case_insensitive(self):
        assert _is_placeholder_title("tEsTrEzEpT 2") is True
        assert _is_placeholder_title("EINZIGES REZEPT") is True
