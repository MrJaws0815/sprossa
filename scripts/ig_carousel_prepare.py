#!/usr/bin/env python3
"""Bereitet Carousel 2 („Ein Weg. Ein Einkauf.") als Instagram-Draft vor.

Prüft Dateien und öffentliche URLs, legt dann einen Carousel-Container mit
Caption an. Veröffentlicht nichts ohne --publish.

Aufruf:
  python3 scripts/ig_carousel_prepare.py --dry-run
  python3 scripts/ig_carousel_prepare.py
  python3 scripts/ig_carousel_prepare.py --publish   # nur nach Freigabe
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
BASE_URL = "https://sprossa.de/media/ig/kw46-carousel2"
LOCAL_DIR = "/home/mrjaws/monatsmenue/dist/carousel/jpg-einkauf"
FILES = ["01.jpg", "02.jpg", "03.jpg", "04.jpg", "05.jpg"]

ALT_TEXTS = [
    "Carousel-Titel: Ein Weg. Ein Einkauf.",
    "Grafik: Supermarkt-Bereiche als Weg durch den Laden",
    "Einkaufsliste in Sprossa, nach Abteilungen gruppiert",
    "Statement: Kein dreimal an der Milch vorbei",
    "Abschluss: Early Access sichern",
]

CAPTION = (
    "Ein Weg. Ein Einkauf.\n\n"
    "Eure Einkaufsliste ist nach Supermarkt-Bereichen sortiert: Obst und Gemüse, "
    "Frische, Kühlregal, Vorrat. Kein dreimal an der Milch vorbei, kein vergessener "
    "Artikel.\n\n"
    "Sprossa bündelt alle Zutaten aus dem Monatsplan in einer Liste – sortiert nach "
    "dem Weg durch den Laden. Early Access → Link in Bio.\n\n"
    "#einkaufsliste #wocheneinkauf #rewe #aldi #edeka #sprossa"
)


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


def check():
    problems = []
    urls = []
    for name in FILES:
        local = os.path.join(LOCAL_DIR, name)
        if not os.path.exists(local):
            problems.append(f"fehlt lokal: {name}")
        else:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0", local],
                capture_output=True, text=True)
            size = out.stdout.strip()
            if size != "1080,1350":
                problems.append(f"{name}: {size} statt 1080,1350")
            if os.path.getsize(local) > 8 * 1024 * 1024:
                problems.append(f"{name}: über 8 MB")
        url = f"{BASE_URL}/{name}"
        urls.append(url)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status != 200 or "image" not in r.headers.get("content-type", ""):
                    problems.append(f"{url}: {r.status} {r.headers.get('content-type')}")
        except Exception as e:
            problems.append(f"{url} nicht erreichbar: {e}")
    if len(FILES) < 2 or len(FILES) > 10:
        problems.append("Carousel braucht 2-10 Bilder")
    if len(CAPTION) > 2200:
        problems.append(f"Caption zu lang: {len(CAPTION)}")
    return urls, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    urls, problems = check()
    print(json.dumps({"slides": len(urls), "caption_len": len(CAPTION),
                      "problems": problems}, ensure_ascii=False, indent=1))
    if problems:
        sys.exit("Abbruch: " + "; ".join(problems))
    if args.dry_run:
        print("Dry-Run: keine API-Aufrufe.")
        return

    # Schritt 1: je Slide einen Kind-Container anlegen (is_carousel_item).
    children = []
    for i, url in enumerate(urls):
        res = claw("clawlink_execute", {
            "integration_id": "instagram",
            "action_id": "post_ig_user_media",
            "confirm": True,
            "input": {
                "ig_user_id": IG_USER_ID,
                "image_url": url,
                "is_carousel_item": True,
                "alt_text": ALT_TEXTS[i] if i < len(ALT_TEXTS) else "",
            },
        })
        sc = res.get("structuredContent") or {}
        out = sc.get("output") or {}
        child = out.get("id") or out.get("creation_id") or (out.get("data") or {}).get("id")
        print(json.dumps({"slide": i + 1, "status": sc.get("status"), "child_id": child,
                          "error": sc.get("message") if sc.get("status") != "succeeded" else None},
                         ensure_ascii=False))
        if not child:
            sys.exit(f"Kind-Container {i + 1} fehlgeschlagen: {sc.get('message') or res}")
        children.append(str(child))

    print(f"Kind-Container: {len(children)}")

    # Schritt 2: Eltern-Container. Meta erwartet media_type=CAROUSEL;
    # die create_carousel_container-Action lehnt den Request ab.
    res = claw("clawlink_execute", {
        "integration_id": "instagram",
        "action_id": "post_ig_user_media",
        "confirm": True,
        "input": {
            "ig_user_id": IG_USER_ID,
            "media_type": "CAROUSEL",
            "caption": CAPTION,
            "children": children,
        },
    })
    sc = res.get("structuredContent") or {}
    out = sc.get("output") or {}
    cid = out.get("id") or out.get("creation_id") or (out.get("data") or {}).get("id")
    print(json.dumps({"status": sc.get("status"), "container_id": cid,
                      "message": sc.get("message")}, ensure_ascii=False))
    if not cid:
        sys.exit("Kein Container angelegt")

    json.dump({"container_id": str(cid), "children": children, "urls": urls},
              open("/tmp/ig_carousel2.json", "w"))

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
                          "media_id": (psc.get("output") or {}).get("id")}, ensure_ascii=False))
    else:
        print("Draft bereit, nicht veröffentlicht.")


if __name__ == "__main__":
    main()
