#!/usr/bin/env python3
"""Baut post.json fuer IG Post 01 und prueft Laengen (Caption 2200, Alt-Text 100)."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "dist" / "social" / "ig-post-01"

CAPTION = """18 Uhr. Alle hungrig. Und niemand weiß, was es gibt.

Das ist selten das Kochen. Das ist die Entscheidung — jeden Abend, genau dann, wenn alle schon müde sind.

Sprossa dreht die Reihenfolge um: Der ganze Monat wird vorher geplant. Rezepte, Portionen, ein Einkauf pro Woche. Wenn ihr abends in die Küche kommt, steht die Antwort schon da.

Was heute auf dem Tisch steht, war vor drei Wochen entschieden.

Sprossa ist gerade im Testbetrieb, eine offene Registrierung gibt es noch nicht. Wer reinsehen will: auf die Waitlist — wir melden uns, sobald ein Platz frei wird.
→ Link in Bio, oder direkt: https://www.sprossa.de/?utm_source=instagram&utm_medium=carousel&utm_campaign=early_access&utm_content=carousel_18uhr

Speichert den Post, wenn ihr die 18-Uhr-Frage kennt. Und schreibt uns in die Kommentare, was bei euch um 18 Uhr auf den Tisch kommt, wenn es schnell gehen muss."""

HASHTAGS = [
    "#essensplan", "#familienalltag", "#18uhrfrage", "#monatsplan", "#essensplanung",
    "#familienkueche", "#wocheneinkauf", "#mealplanning", "#kochenmitkindern", "#sprossa",
]

ALT = [
    "Creme-Grafik mit Sprossa-Logo: „Alle hungrig. Keine Antwort.“ Label: Die 18-Uhr-Frage.",
    "Grafik mit drei Zeitstempeln: 18:00 alle in der Küche, 18:10 wieder Nudeln, 18:45 gegessen.",
    "Screenshot der Sprossa-App: Monatsplan mit vier Wochen und je sieben Gerichten.",
    "Screenshot der Sprossa-App: eine Woche mit sieben geplanten Gerichten als Karten.",
    "Dunkelgrüne Grafik: „Der Plan entscheidet. Ihr kocht nur noch.“",
    "Creme-Grafik: „Die Beta läuft. Die Plätze sind begrenzt.“ Button: Early Access sichern.",
]

SLIDES = [
    "01-cover.jpg", "02-szene.jpg", "03-plan.jpg",
    "04-woche.jpg", "05-statement.jpg", "06-cta.jpg",
]

full_caption = CAPTION + "\n\n" + " ".join(HASHTAGS)

data = {
    "post_id": "ig-post-01",
    "account": "@team_sprossa",
    "format": "carousel",
    "slide_count": len(SLIDES),
    "scheduled": "2026-11-16T19:45:00+01:00",
    "iso_week": 47,
    "theme": "Die 18-Uhr-Frage",
    "hook": "18 Uhr. Alle hungrig. Und niemand weiß, was es gibt.",
    "core_message": "Es fehlt nicht am Kochen, sondern an der Entscheidung — der Monat ist vorher geplant.",
    "cta": "Waitlist / Early Access",
    "link": "https://www.sprossa.de/?utm_source=instagram&utm_medium=carousel&utm_campaign=early_access&utm_content=carousel_18uhr",
    "utm": {
        "source": "instagram",
        "medium": "carousel",
        "campaign": "early_access",
        "content": "carousel_18uhr",
    },
    "files": {
        "upload": [f"jpg/{s}" for s in SLIDES],
        "master": [f"png/{s.replace('.jpg', '.png')}" for s in SLIDES],
        "source_html": "carousel.html",
    },
    "caption": full_caption,
    "caption_without_hashtags": CAPTION,
    "hashtags": HASHTAGS,
    "alt_texts": ALT,
    "first_comment": "Falls ihr euch fragt, wie so ein Monat entsteht: fünf Minuten einstellen, dann steht der Plan. Der Rest ist Kochen.",
    "publish": False,
    "status": "awaiting_approval",
}

assert len(full_caption) <= 2200, len(full_caption)
for i, a in enumerate(ALT, 1):
    assert len(a) <= 100, (i, len(a), a)

(BASE / "post.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Caption gesamt: {len(full_caption)} Zeichen (Limit 2200)")
print(f"Caption ohne Hashtags: {len(CAPTION)} Zeichen")
print("Alt-Texte:", [len(a) for a in ALT])
print("geschrieben:", BASE / "post.json")
