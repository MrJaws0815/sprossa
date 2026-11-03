#!/usr/bin/env python3
"""
Sprossa – Obsidian-Pfade auf den Netzlaufwerk-Share umstellen.

Ersetzt lokale Pfade in allen Markdown-Notizen des Sprossa-Vaults durch die
Pfade auf \\\\HOMENAS\\Sprossa. Erzeugt vorher ein Backup der geänderten Dateien.

Aufruf:
  python3 scripts/update_obsidian_paths.py --dry-run   # nur anzeigen
  python3 scripts/update_obsidian_paths.py             # schreiben
  python3 scripts/update_obsidian_paths.py --backup-dir ~/sprossa-pfad-backup

Wichtig: Obsidian-Links in [[]] werden NICHT angefasst – die beziehen sich auf
Notizen, nicht auf Dateien. Es geht nur um konkrete Dateipfade im Fließtext.
"""

import argparse
import datetime as dt
import os
import shutil
import sys

VAULT = "/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa"
NAS = r"\\HOMENAS\Sprossa"

# Lokaler Pfad  ->  Pfad auf dem Share
# Reihenfolge zählt: längere Präfixe zuerst, sonst greift /dist/pins vor
# /dist/pins-strategisch und produziert kaputte Pfade.
MAPPINGS = [
    ("/home/mrjaws/monatsmenue/dist/pins-strategisch", NAS + r"\02_Content\Pins\strategisch"),
    ("/home/mrjaws/monatsmenue/dist/pins",             NAS + r"\02_Content\Pins\serien"),
    ("/home/mrjaws/monatsmenue/dist/reels",            NAS + r"\02_Content\Reels\Keyframes"),
    ("/home/mrjaws/monatsmenue/dist/footage",          NAS + r"\02_Content\Reels\Footage"),
    ("/home/mrjaws/monatsmenue/dist/landing",          NAS + r"\03_Technik\Landingpage-Build"),
    ("/home/mrjaws/monatsmenue/dist",                  NAS + r"\02_Content"),
    ("/home/mrjaws/monatsmenue/backups",               NAS + r"\03_Technik\Backups"),
    ("/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa/03 Marke & Design/Social-Assets",
     NAS + r"\01_Marke_und_Design\Social-Assets"),
    ("/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa/03 Marke & Design/Logo",
     NAS + r"\01_Marke_und_Design\Logo"),
    ("/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa/03 Marke & Design",
     NAS + r"\01_Marke_und_Design"),
]

# Diese Notizen werden bewusst nicht angefasst: sie dokumentieren, WO die
# Quelldateien lokal liegen, und sollen das auch weiterhin tun.
SKIP = {
    "Sprossa - Design-Preview-Hosting.md",  # beschreibt lokalen Preview-Server
    "Sprossa - UX-UI Review 31.10.2026 - App-Seiten.md",  # Code-Review, lokale Pfade korrekt
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup-dir", default=None)
    ap.add_argument("--vault", default=VAULT)
    args = ap.parse_args()

    backup_dir = args.backup_dir
    if not args.dry_run and not backup_dir:
        backup_dir = os.path.expanduser(
            "~/sprossa-obsidian-backup-" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        )

    changed = []
    for root, _dirs, files in os.walk(args.vault):
        for name in sorted(files):
            if not name.endswith(".md") or name in SKIP:
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()

            new = text
            hits = []
            for local, remote in MAPPINGS:
                if local in new:
                    count = new.count(local)
                    new = new.replace(local, remote)
                    hits.append((local, count))

            if not hits:
                continue

            rel = os.path.relpath(path, args.vault)
            changed.append((rel, hits, path, text, new))

    if not changed:
        print("Keine lokalen Pfade gefunden – nichts zu tun.")
        return 0

    print(f"{len(changed)} Notiz(en) betroffen:\n")
    for rel, hits, _path, _old, _new in changed:
        print(f"  {rel}")
        for local, count in hits:
            print(f"      {count}× {local}")

    if args.dry_run:
        print("\n--dry-run: nichts geschrieben.")
        return 0

    os.makedirs(backup_dir, exist_ok=True)
    for rel, _hits, path, old, new in changed:
        flat = rel.replace(os.sep, "__")
        shutil.copy2(path, os.path.join(backup_dir, flat))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)

    print(f"\n{len(changed)} Notiz(en) aktualisiert.")
    print(f"Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
