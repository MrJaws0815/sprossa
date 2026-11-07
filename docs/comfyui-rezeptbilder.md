# Rezeptbilder selbst generieren mit ComfyUI

**Stand:** 07.11.2026 · **Status:** geplant, nicht eingerichtet

## Warum überhaupt

Die Bildbeschaffung über Openverse (siehe Skill `licensed-image-sourcing`) hat zwei
strukturelle Grenzen, die sich nicht wegoptimieren lassen:

1. **Wikimedia drosselt.** Originale antworten mit HTTP 429, Thumbnails nur in
   Standardbreiten (320/640/800/1024/1280/2560), andere mit HTTP 400. Bei 320 Rezepten
   läuft man dauerhaft am Limit.
2. **Die Motive passen oft nicht.** Im Test: „Hähnchen-Curry" zeigte Garnelen, auf dem
   Apfelkuchen stand eine Guinness-Flasche mit Logo. Von vier geprüften Bildern war
   eines brauchbar.

Eigene Generierung löst beides: kein Rate-Limit, garantiert das richtige Gericht, keine
Namensnennung, einheitlicher Look.

## Was es kostet

| Posten | Kosten |
|---|---|
| ComfyUI (Software) | 0 € — Open Source |
| SDXL base 1.0 (6,5 GB) | 0 € — CreativeML OpenRAIL++-M, kommerzielle Nutzung erlaubt |
| Flux.1-schnell (12 GB) | 0 € — Apache 2.0, kommerzielle Nutzung erlaubt |
| Flux.1-dev | 0 €, aber **Lizenz nur für nicht-kommerzielle Nutzung** — für Sprossa ungeeignet |
| Strom | RTX 4090 ≈ 350 W × ~4 s/Bild → 320 Bilder ≈ 21 min ≈ 0,13 kWh ≈ **4 Cent** |
| Zeit | Setup ~1 h, Generierung inkl. Sichtprüfung ~2 h |

Realistisch also **unter 10 Cent** für alle 320 Bilder. Der Aufwand liegt im Setup, nicht im Geld.

**Hardware-Voraussetzung:** ≥8 GB VRAM für SDXL, ≥12 GB für Flux. Der Desktop-PC erfüllt
das laut Projektinhaber; die GPU war bei der Prüfung nicht erreichbar (Rechner aus,
`192.168.178.4` antwortete weder auf Ping noch auf Port 22).

## Einrichtung (Windows-Desktop, NVIDIA)

1. **ComfyUI installieren** — entweder Desktop-Installer
   (`https://download.comfy.org/windows/nsis/x64`) oder Portable-Variante von
   `github.com/comfyanonymous/ComfyUI/releases`.
   Für den Agenten-Betrieb ist der Weg über die CLI sauberer:
   ```
   pipx install comfy-cli
   comfy --skip-prompt tracking disable
   comfy --skip-prompt install --nvidia
   ```
2. **Modell laden** (SDXL als Standard, Flux-schnell als Upgrade):
   ```
   comfy model download --url "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" --relative-path models/checkpoints
   ```
3. **Im LAN erreichbar machen** — entscheidend, sonst kommt der Pi nicht dran:
   ```
   comfy launch -- --listen 0.0.0.0 --port 8188
   ```
   Danach vom Pi prüfen: `curl http://192.168.178.4:8188/system_stats`.
   Windows-Firewall muss Port 8188 eingehend erlauben.
4. **Als Dienst einrichten**, damit der Rechner nach einem Neustart wieder erreichbar ist
   (Aufgabenplanung: „Bei Anmeldung" → `comfy launch -- --listen 0.0.0.0`).

## Prompt-Strategie

Pro Rezept aus Titel, Zutaten und Küche:

```
<Gericht>, <Hauptzutaten>, German home cooking, food photography,
overhead shot, natural window light, ceramic plate, rustic wooden table,
shallow depth of field, appetizing, no text, no people, no hands
```

Negativ-Prompt: `text, watermark, logo, people, hands, blurry, plastic, cartoon, raw meat`

Zwei Dinge, die SDXL typisch falsch macht und die man im Prompt ausschließen muss:
Hände und Schrift. Beides sofort als KI-Bild erkennbar.

## Ablauf im Betrieb

1. Rezepte aus der DB ziehen (Titel + Zutaten).
2. Prompt bauen, per `run_batch.py` aus dem `comfyui`-Skill generieren
   (4 Bilder je Rezept, Seed variieren).
3. **Vision-Prüfung wie bei Openverse** — dasselbe Kontaktabzug-Verfahren, nur mit den
   eigenen Varianten. Beste Note gewinnt.
4. Ausgabe auf 1200×800 zuschneiden, WebP q84, unter `frontend/public/food/`.
5. Kein Credit nötig — aber in `docs/bildquellen.md` vermerken, dass die Bilder
   KI-generiert sind (Transparenz gegenüber Nutzern).

## Risiken

| Risiko | Umgang |
|---|---|
| SDXL-Food wirkt „plastisch" | Flux-schnell liefert realistischere Texturen; ggf. nur für Problemfälle |
| Gerichte sehen nicht wie das Rezept aus | Prompt aus Zutatenliste bauen, nicht aus dem Titel allein |
| Bilder wirken untereinander zu ähnlich | Seed variieren, Perspektive im Prompt wechseln (overhead / 45° / close-up) |
| Rechner muss zum Generieren laufen | Generierung ist einmalig; Ergebnisse liegen als statische Dateien im Repo |
| Strom/Abwärme bei 320 Bildern | ~21 min GPU-Zeit, unkritisch |

## Entscheidung

ComfyUI ist die **bessere** Lösung, sobald der Desktop erreichbar ist — aber nicht die
schnellere. Der Openverse-Batch läuft jetzt als Zwischenlösung; sobald eigene Bilder
existieren, werden die Dateien in `frontend/public/food/` schlicht ersetzt. Die
Bildanzeige in der App bleibt identisch.
