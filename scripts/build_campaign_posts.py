"""Baut die beiden Kampagnen-Carousels, die die freien IG-Slots belegen.

16.11.2026 — „Der Dezember ist schon entschieden" (5 Slides, typografisch)
26.11.2026 — „Drei Gerichte, die Kinder wirklich essen" (5 Slides, Katalog-Rezepte)
"""
from pathlib import Path

BASE = Path("/home/mrjaws/monatsmenue/dist/social/campaign")

SPROSS = """<svg width="30" height="39" viewBox="0 0 100 130" fill="none" aria-hidden="true">
          <path d="M50 126 C44 96 46 66 52 46" stroke="{c}" stroke-width="9" stroke-linecap="round"></path>
          <path d="M50 52 C34 44 20 28 14 10 C32 6 48 26 50 52 Z" fill="{c}"></path>
          <path d="M50 52 C66 44 80 28 86 10 C68 6 52 26 50 52 Z" fill="{c}"></path>
        </svg>"""


def brandbar(kicker: str, color: str = "#3A7D44", wordmark_color: str = "") -> str:
    wm = f' style="color:{wordmark_color}"' if wordmark_color else ""
    return f"""    <div class="brandbar">
      <div class="mark">
        {SPROSS.format(c=color)}
        <div class="wordmark"{wm}>sprossa<span class="dot">.</span></div>
      </div>
      <div class="kicker">{kicker}</div>
    </div>"""


SWATCH = """    <div class="swatches"><i style="background:#3A7D44"></i><i style="background:#2C5F34"></i><i style="background:#D96B4A"></i><i style="background:#E6A23C"></i></div>"""


def page(title: str, slides: list[str]) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="../fonts/fonts.css">
<link rel="stylesheet" href="../base.css">
</head>
<body>
<div class="deck">

{chr(10).join(slides)}

</div>
</body>
</html>
"""


# ── Post 1: Der Dezember ist entschieden ───────────────────────────────────

def dezember() -> str:
    days = "".join(f'<i class="on">{d}</i>' for d in range(1, 29))
    s1 = f"""  <section class="slide cover" data-name="01-cover">
{brandbar("Adventszeit")}
    <div class="body">
      <span class="stamp"><i class="dot"></i>Der nächste Monat</span>
      <h1>Der Dezember ist<br>schon <em>entschieden.</em></h1>
      <p class="lead">Nicht am 1. Dezember. Sondern jetzt — an einem Abend, an dem niemand hungrig in der Küche steht.</p>
    </div>
    <div class="foot"><span>28 Abende, ein Einkauf</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>"""

    s2 = f"""  <section class="slide" data-name="02-kalender">
{brandbar("Der ganze Monat")}
    <div class="body">
      <h2>28 Abende. Keiner davon <em>offen.</em></h2>
      <div class="cal">{days}</div>
      <p class="lead">Jedes Feld steht für ein Gericht, das vorher feststeht — nicht für einen Termin, den man abends erfinden muss.</p>
    </div>
    <div class="foot"><span>Ein Monat, am Stück geplant</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>"""

    s3 = f"""  <section class="slide" style="background:var(--green-soft)" data-name="03-einkauf">
{brandbar("Der Unterschied")}
    <div class="body">
      <h2>Ein Einkauf pro Woche statt <em>fünf.</em></h2>
      <div class="numlist">
        <div class="row"><div class="num">1</div><div class="t">Alle Zutaten des Monats stehen vorher fest — nichts wird unterwegs vergessen.</div></div>
        <div class="row"><div class="num">2</div><div class="t">Die Liste ist nach dem Weg durch den Laden sortiert, nicht nach Rezepten.</div></div>
        <div class="row"><div class="num">3</div><div class="t">Was zusammenpasst, wird zusammen gekauft — und zusammen gekocht.</div></div>
      </div>
    </div>
    <div class="foot"><span>Sortiert nach Supermarkt-Bereichen</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>"""

    s4 = f"""  <section class="slide statement" data-name="04-statement">
{brandbar("Die Idee", color="#FAF6EF", wordmark_color="#FAF6EF")}
    <div class="body">
      <h2>Nicht mehr Disziplin.<br><em>Eine Entscheidung</em>, früher getroffen.</h2>
      <p class="sub">Der Monatsplan nimmt die Frage weg, bevor sie entsteht. Was übrig bleibt, ist kochen — nicht ausdenken.</p>
    </div>
    <div class="foot"><span>Sprossa · Testbetrieb</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>"""

    s5 = f"""  <section class="slide cta" data-name="05-cta">
{brandbar("Early Access", color="#FAF6EF", wordmark_color="#FAF6EF")}
    <div class="body">
      <h2>Der nächste Monat ist geplant, <em>bevor</em> er anfängt.</h2>
      <p class="sub">Die Beta läuft, die Plätze sind begrenzt. Wer reinsehen will, kommt auf die Waitlist.</p>
      <span class="url">sprossa.de</span>
    </div>
    <div class="foot"><span>Kein Abo nötig, um zu speichern.</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>"""
    return page("Sprossa — Der Dezember ist entschieden", [s1, s2, s3, s4, s5])


# ── Post 2: Drei Gerichte, die Kinder wirklich essen ───────────────────────

DISHES = [
    ("Currywurst-Sauce mit Pommes", "15 Min", "Der schnellste Abend der Woche.",
     "Rührt die Sauce selbst an: Ketchup, Currypulver und Worcestershire in einer Tasse verrühren, erst daran riechen, dann mit dem Finger probieren. Die Würstchen schneiden Schulkinder mit der Küchenschere in Stücke; die Pfanne mit der heissen Butter bleibt bei einem Erwachsenen."),
    ("Frikadellen mit Kartoffelstampf und Gurkensalat", "40 Min", "Der Klassiker, der nie übrig bleibt.",
     "Die Hackmasse mit den Händen durchkneten, bis sie zusammenhält — kalt, klebrig und genau das, was Kinder ohnehin tun wollen; daraus acht flache Frikadellen formen und laut mitzählen. Die Pfanne mit dem heissen Rapsöl gehört einem Erwachsenen."),
    ("Brokkoli-Käse-Gratin mit Knusperkruste", "35 Min", "Gemüse, das tatsächlich gegessen wird.",
     "Paniermehl und Parmesan mit den Fingern mischen und über den Brokkoli streuen — die Krümel sollen ungleich liegen, das gibt die knusprigen Ecken. Die Käsesauce am Herd rührt ein Erwachsener, sie spritzt beim Schmelzen."),
]


def kinder() -> str:
    s1 = f"""  <section class="slide cover" data-name="01-cover">
{brandbar("Aus dem Rezeptkatalog")}
    <div class="body">
      <span class="stamp"><i class="dot"></i>Kinderfreundlich</span>
      <h1>Drei Gerichte,<br>die Kinder <em>wirklich</em> essen.</h1>
      <p class="lead">Kein „probier mal". Sondern drei Abende, an denen niemand diskutiert.</p>
    </div>
    <div class="foot"><span>Alle aus unserem Katalog</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>"""

    slides = [s1]
    for i, (title, time, why, tip) in enumerate(DISHES, start=2):
        slides.append(f"""  <section class="slide recipe" data-name="0{i}-{title.split()[0].lower()}">
{brandbar(f"Gericht {i-1} von 3")}
    <div class="body">
      <div class="dish">4 Portionen · {time}</div>
      <h2 style="font-size:62px">{title}</h2>
      <div class="dishcard">
        <div class="t">{why}</div>
        <div class="m"><span class="pill solid">4 Portionen</span><span class="pill">{time}</span></div>
      </div>
      <div class="tipbox">
        <div class="lab">Mit Kindern kochen</div>
        <p>{tip}</p>
      </div>
    </div>
    <div class="foot"><span>Aus dem Sprossa-Katalog</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>""")

    slides.append(f"""  <section class="slide cta" data-name="05-cta">
{brandbar("Speichern lohnt sich", color="#FAF6EF", wordmark_color="#FAF6EF")}
    <div class="body">
      <h2>Drei Abende, an denen niemand <em>diskutiert.</em></h2>
      <p class="sub">Sprossa plant den ganzen Monat — mit Rezepten, die die Familie wirklich isst, und einer Einkaufsliste für alles.</p>
      <span class="url">sprossa.de</span>
    </div>
    <div class="foot"><span>Early Access über die Waitlist</span><span class="handle">@team_sprossa</span></div>
{SWATCH}
  </section>""")
    return page("Sprossa — Drei Gerichte für Kinder", slides)


def main() -> None:
    (BASE / "01-dezember").mkdir(parents=True, exist_ok=True)
    (BASE / "02-kinder").mkdir(parents=True, exist_ok=True)
    (BASE / "01-dezember" / "post.html").write_text(dezember(), encoding="utf-8")
    (BASE / "02-kinder" / "post.html").write_text(kinder(), encoding="utf-8")
    print("geschrieben: 01-dezember/post.html, 02-kinder/post.html")


if __name__ == "__main__":
    main()
