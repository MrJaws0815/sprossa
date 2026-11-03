#!/usr/bin/env python3
"""Bereitet ein Instagram-Reel als Draft-Container vor (veröffentlicht nichts).

Prüft lokale Datei + öffentliche URL, legt dann über ClawLink einen
Reels-Container mit Caption an. Der Container verfällt nach ~24 h, wenn er
nicht publiziert wird.

Aufruf:
  python3 scripts/ig_reel_prepare.py cookonce
  python3 scripts/ig_reel_prepare.py deutsch --dry-run
  python3 scripts/ig_reel_prepare.py 18uhr --publish   # nur nach Freigabe!

Slugs: cookonce, deutsch, 18uhr
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

import yaml

IG_USER_ID = "28764096343282095"
CONFIG = os.path.expanduser("~/.hermes/profiles/sprossa-pm/config.yaml")
MEDIA_BASE = "https://sprossa.de/media/reels"

REELS = {
    "cookonce": {
        "title": "Cook once, eat twice",
        "date": "2026-11-09",
        "file": "reel-cookonce.mp4",
        "caption": (
            "Einmal kochen, zweimal essen: Aus einem Blech Ofengemüse wird montags ein Teller mit Feta, "
            "mittwochs eine Bowl. Zwei Abende, ein Aufwand.\n\n"
            "Sprossa plant bewusst Gerichte ein, die sich lohnen – und rechnet die Portionen so, dass am "
            "zweiten Abend nichts fehlt. Bei vier Cook-once-Gerichten im Monat sind das vier Abende, die "
            "ihr zurückbekommt.\n\n"
            "Early Access → Link in Bio.\n\n"
            "#cookonceeattwice #mealprep #familienalltag #zeitersparnis #sprossa"
        ),
    },
    "deutsch": {
        "title": "Deutsch, nicht übersetzt",
        "date": "2026-11-12",
        "file": "reel-deutsch.mp4",
        "caption": (
            "Deutsche Rezepte. Deutsche Zutaten. Deutsche Mengen.\n\n"
            "Viele Essensplaner kommen aus den USA: Rezepte in Cups, Zutaten, die es im deutschen "
            "Supermarkt nicht gibt, Einkaufslisten ohne Gang-Reihenfolge.\n\n"
            "Sprossa ist von Grund auf deutsch: Zutaten, die es bei Rewe, Aldi, Edeka und Lidl wirklich "
            "gibt, Mengen in Gramm, ein Samstagseinkauf, der zur Woche passt. Kein Übersetzen, kein Umrechnen.\n\n"
            "Early Access → Link in Bio.\n\n"
            "#deutscheküche #essensplaner #wocheneinkauf #rewe #aldi #sprossa"
        ),
    },
    "18uhr": {
        "title": "Die 18-Uhr-Frage",
        "date": "2026-11-16",
        "file": "reel-18uhr.mp4",
        "caption": (
            "18 Uhr. Alle hungrig. Und niemand weiß, was es gibt.\n\n"
            "Sprossa dreht die Frage um: Der ganze Monat ist vorab geplant – mit Rezepten, die zu eurem "
            "Alltag passen, und einer Einkaufsliste, die alles zusammenfasst.\n\n"
            "Was heute auf dem Tisch steht, war vor drei Wochen schon entschieden. Early Access → Link in Bio.\n\n"
            "#essensplan #familienalltag #18uhrfrage #monatsplan #sprossa #mealplanning"
        ),
    },
}

LOCAL_DIR = "/home/mrjaws/monatsmenue/dist/reels/kw46"


def claw(rpc_name, args, timeout=240):
    cfg = yaml.safe_load(open(CONFIG, encoding="utf-8"))
    srv = cfg["mcp_servers"]["clawlink"]
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": rpc_name, "arguments": args}}
    req = urllib.request.Request(
        srv["url"], data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream",
                 "x-clawlink-api-key": srv["headers"]["x-clawlink-api-key"]})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            try:
                d = json.loads(line)
                if "result" in d:
                    return d["result"]
            except json.JSONDecodeError:
                pass
    return {}


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,codec_name,duration",
         "-of", "json", path],
        capture_output=True, text=True)
    if out.returncode != 0:
        return None
    st = (json.loads(out.stdout or "{}").get("streams") or [{}])[0]
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", choices=sorted(REELS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true",
                    help="Container sofort veröffentlichen (nur nach Freigabe)")
    args = ap.parse_args()

    reel = REELS[args.slug]
    local = os.path.join(LOCAL_DIR, reel["file"])
    public = f"{MEDIA_BASE}/{reel['file']}"

    problems = []
    if not os.path.exists(local):
        problems.append(f"lokale Datei fehlt: {local}")
    else:
        st = probe(local)
        if not st:
            problems.append("ffprobe konnte die Datei nicht lesen")
        else:
            w, h = int(st.get("width", 0)), int(st.get("height", 0))
            dur = float(st.get("duration", 0) or 0)
            if (w, h) != (1080, 1920):
                problems.append(f"Auflösung {w}x{h} statt 1080x1920")
            if not (3 <= dur <= 90):
                problems.append(f"Dauer {dur:.1f}s außerhalb 3–90s")

    try:
        req = urllib.request.Request(public, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            ctype = r.headers.get("content-type", "")
            if r.status != 200 or "video" not in ctype:
                problems.append(f"öffentliche URL antwortet {r.status} / {ctype}")
    except Exception as e:
        problems.append(f"öffentliche URL nicht erreichbar: {e}")

    print(json.dumps({"slug": args.slug, "title": reel["title"], "date": reel["date"],
                      "public_url": public, "caption_len": len(reel["caption"]),
                      "problems": problems}, ensure_ascii=False, indent=1))

    if problems:
        sys.exit("Vorbereitung abgebrochen: " + "; ".join(problems))
    if args.dry_run:
        print("Dry-Run: keine API-Aufrufe.")
        return

    res = claw("clawlink_execute", {
        "integration_id": "instagram",
        "action_id": "post_ig_user_media",
        "confirm": True,
        "input": {
            "ig_user_id": IG_USER_ID,
            "media_type": "REELS",
            "video_url": public,
            "caption": reel["caption"],
            "share_to_feed": True,
        },
    })
    sc = res.get("structuredContent") or {}
    out = sc.get("output") or {}
    cid = out.get("id") or out.get("creation_id") or (out.get("data") or {}).get("id")
    status = sc.get("status")
    print(json.dumps({"status": status, "container_id": cid,
                      "summary": (sc.get("display") or {}).get("summary")},
                     ensure_ascii=False, indent=1))
    if not cid:
        sys.exit("Kein Container angelegt")

    state = f"/tmp/ig_reel_{args.slug}.json"
    json.dump({"slug": args.slug, "container_id": str(cid), "date": reel["date"],
               "public_url": public}, open(state, "w"), ensure_ascii=False)

    if args.publish:
        pub = claw("clawlink_execute", {
            "integration_id": "instagram",
            "action_id": "post_ig_user_media_publish",
            "confirm": True,
            "input": {"ig_user_id": IG_USER_ID, "creation_id": str(cid),
                      "max_wait_seconds": 300, "poll_interval_seconds": 5},
        })
        psc = pub.get("structuredContent") or {}
        print(json.dumps({"publish_status": psc.get("status"),
                          "media_id": (psc.get("output") or {}).get("id")},
                         ensure_ascii=False))
    else:
        print(f"Draft bereit: {state} (nicht veröffentlicht)")


if __name__ == "__main__":
    main()
