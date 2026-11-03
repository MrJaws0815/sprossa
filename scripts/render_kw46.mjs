#!/usr/bin/env node
/**
 * Sprossa – KW46 Reels: Storyboard → 1080×1920 Keyframes.
 *
 * Baut aus einer Szenenliste ein HTML-Storyboard (je Szene ein 1080×1920-Frame),
 * rendert jeden Frame per Chromium-Screenshot und schreibt ein Manifest mit
 * Dauer + Kamerafahrt pro Frame. Das Manifest füttert render_footage.py.
 *
 * Kein Kamerafootage: alle Szenen sind Motion Graphics aus echten App-Screens,
 * CI-Typografie und klar als Grafik erkennbaren Elementen.
 *
 * Aufruf: node scripts/render_kw46.mjs
 */

import { chromium } from "playwright-core";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const ROOT = "/home/mrjaws/monatsmenue";
const OUT = path.join(ROOT, "dist/reels/kw46");
const FRAMES = path.join(OUT, "frames");
const SCREENS = path.join(ROOT, "dist/carousel/screens");
const HTML = path.join(OUT, "storyboard.html");

fs.mkdirSync(FRAMES, { recursive: true });

/* ---------------------------------------------------------------- Szenen */

const S = (o) => o;

const REELS = {
  "reel-18uhr": [
    S({ kind: "hook", dur: 2.0, motion: "in", num: "18:04",
        lines: ["Alle hungrig.", "Niemand weiß, was es gibt."] }),
    S({ kind: "statement", dur: 2.8, motion: "out", kicker: "Die Frage",
        lines: [{ t: "Jeden." }, { t: "Tag.", accent: "terra" }] }),
    S({ kind: "screen", dur: 3.2, motion: "in", screen: "plan-big.png", cardH: 900,
        kicker: "Wochenplan", lines: [{ t: "Der Monat ist" }, { t: "entschieden." }] }),
    S({ kind: "screen", dur: 3.2, motion: "out", screen: "recipes.png", cardH: 640,
        kicker: "Rezept", lines: [{ t: "Nicht die Frage." }, { t: "Das Rezept." }] }),
    S({ kind: "statement", dur: 3.0, motion: "in", kicker: "Seit drei Wochen",
        lines: [{ t: "Seit drei Wochen" }, { t: "entschieden.", accent: "green" }] }),
    S({ kind: "screen", dur: 3.2, motion: "out", screen: "plan-big.png", cardH: 900,
        flip: true, kicker: "Heute",
        lines: [{ t: "Heute steht fest," }, { t: "was es gibt." }] }),
    S({ kind: "cta", dur: 3.6, motion: "in",
        lines: [{ t: "Sprossa plant euren Monat." }, { t: "Ihr kocht nur noch.", accent: "green" }] }),
    S({ kind: "endcard", dur: 3.8, motion: "out" }),
  ],

  "reel-deutsch": [
    S({ kind: "hook", dur: 2.0, motion: "in", num: "1 cup?",
        lines: ["Wie viel ist das?"] }),
    S({ kind: "statement", dur: 2.6, motion: "out", kicker: "Aus dem US-Rezept",
        lines: [{ t: "Cups. Ounces." }, { t: "Fahrenheit." }] }),
    S({ kind: "statement", dur: 2.6, motion: "in", kicker: "Und dann",
        lines: [{ t: "Zutaten, die es" }, { t: "hier nicht gibt." }] }),
    S({ kind: "screen", dur: 3.2, motion: "out", screen: "grocery-big.png", cardH: 900,
        kicker: "Einkaufsliste", lines: [{ t: "740 g" }, { t: "Champignons.", accent: "green" }] }),
    S({ kind: "screen", dur: 3.2, motion: "in", screen: "grocery-big.png", cardH: 900,
        flip: true, kicker: "Gang-Reihenfolge",
        lines: [{ t: "Sortiert nach" }, { t: "Gang." }] }),
    S({ kind: "statement", dur: 2.8, motion: "out", kicker: "Wo ihr einkauft",
        lines: [{ t: "Rewe · Aldi ·" }, { t: "Edeka · Lidl" }] }),
    S({ kind: "screen", dur: 3.2, motion: "in", screen: "plan-big.png", cardH: 900,
        kicker: "Monatsplan", lines: [{ t: "Deutscher" }, { t: "Monatsplan." }] }),
    S({ kind: "screen", dur: 3.0, motion: "out", screen: "recipes.png", cardH: 640,
        flip: true, kicker: "Rezepte", lines: [{ t: "Deutsche Rezepte." }] }),
    S({ kind: "statement", dur: 2.6, motion: "in", kicker: "Kein Umrechnen",
        lines: [{ t: "Kein Umrechnen." }, { t: "Kein Suchen." }] }),
    S({ kind: "statement", dur: 3.0, motion: "out", kicker: "Sprossa",
        lines: [{ t: "Gramm. Deutsch." }, { t: "Sortiert.", accent: "green" }] }),
    S({ kind: "endcard", dur: 3.6, motion: "in" }),
  ],

  "reel-cookonce": [
    S({ kind: "hook", dur: 2.0, motion: "in", num: "1 → 2",
        lines: ["Einmal kochen.", "Zweimal essen."] }),
    S({ kind: "split", dur: 2.8, motion: "out", kicker: "Cook once",
        left: "1", right: "2", badge: "COOK ONCE" }),
    S({ kind: "screen", dur: 3.2, motion: "in", screen: "plan-big.png", cardH: 900,
        kicker: "Plan-Slot", lines: [{ t: "Ein Slot." }, { t: "Zwei Abende." }] }),
    S({ kind: "chip", dur: 2.8, motion: "out", kicker: "Der zweite Abend",
        chip: "RESTE-TAG", lines: [{ t: "Ist eingeplant." }] }),
    S({ kind: "statement", dur: 2.8, motion: "in", kicker: "Kein Aufwärmen",
        lines: [{ t: "Kein Reste-Gefühl." }, { t: "Ein neues Gericht.", accent: "terra" }] }),
    S({ kind: "screen", dur: 3.0, motion: "out", screen: "recipes.png", cardH: 640,
        flip: true, kicker: "Ein Rezept",
        lines: [{ t: "Ein Rezept." }, { t: "Zwei Gerichte." }] }),
    S({ kind: "counter", dur: 3.0, motion: "in", kicker: "Im Monat",
        num: "4", unit: "Abende", lines: [{ t: "Ein Kochaufwand." }] }),
    S({ kind: "statement", dur: 2.8, motion: "out", kicker: "Zwei Abende",
        lines: [{ t: "Zwei Abende." }, { t: "Ein Einkauf." }] }),
    S({ kind: "cta", dur: 3.4, motion: "in",
        lines: [{ t: "Abends 20 Minuten" }, { t: "zurück.", accent: "green" }] }),
    S({ kind: "endcard", dur: 3.4, motion: "out" }),
  ],
};

/* ------------------------------------------------------------------ HTML */

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");

function linesHTML(lines) {
  return lines
    .map((l) => {
      const t = typeof l === "string" ? l : l.t;
      const a = typeof l === "string" ? null : l.accent;
      return `<span class="ln${a ? " " + a : ""}">${esc(t)}</span>`;
    })
    .join("");
}

function brand() {
  return `<div class="brand"><img class="mark" src="spross.svg" alt=""><span class="word">sprossa</span></div>`;
}

function sceneHTML(s, i, top) {
  const kicker = s.kicker ? `<div class="kicker"><i></i>${esc(s.kicker)}</div>` : "";
  const body = (() => {
    switch (s.kind) {
      case "hook":
        return `<div class="stack hook">${kicker}
          <div class="num">${esc(s.num)}</div>
          <div class="lines">${linesHTML(s.lines)}</div></div>`;
      case "statement":
        return `<div class="stack mid">${kicker}
          <div class="lines big">${linesHTML(s.lines)}</div></div>`;
      case "screen": {
        const cardTop = s.flip ? 240 : 820;
        const txtTop = s.flip ? cardTop + s.cardH + 64 : 300;
        const card = `<div class="card" style="height:${s.cardH}px;top:${cardTop}px">
            <img src="../../carousel/screens/${s.screen}" alt=""></div>`;
        const txt = `<div class="stack" style="top:${txtTop}px">${kicker}
            <div class="lines mid2">${linesHTML(s.lines)}</div></div>`;
        return s.flip ? card + txt : txt + card;
      }
      case "cta":
        return `<div class="stack mid">${kicker}
          <div class="lines big">${linesHTML(s.lines)}</div>
          <div class="pill">Early Access <span class="arw">→</span></div></div>`;
      case "endcard":
        return `<div class="end">
            <img class="endmark" src="spross.svg" alt="">
            <div class="endword">sprossa</div>
            <div class="endline">Euer Monat, klug geplant.</div>
            <div class="endcta">Early Access</div>
            <div class="endurl">sprossa.de</div>
          </div>`;
      case "split":
        return `<div class="stack mid">${kicker}
          <div class="split">
            <div class="snum">${esc(s.left)}</div>
            <svg class="sarrow" viewBox="0 0 120 40" aria-hidden="true">
              <path d="M4 20 H104" stroke="#26302B" stroke-width="6" stroke-linecap="round"/>
              <path d="M86 6 L106 20 L86 34" fill="none" stroke="#26302B" stroke-width="6"
                    stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="snum">${esc(s.right)}</div>
          </div>
          <div class="badge">${esc(s.badge)}</div></div>`;
      case "chip":
        return `<div class="stack mid">${kicker}
          <div class="chip">${esc(s.chip)}</div>
          <div class="lines mid2">${linesHTML(s.lines)}</div></div>`;
      case "counter":
        return `<div class="stack mid">${kicker}
          <div class="counter"><span class="cnum">${esc(s.num)}</span><span class="cunit">${esc(s.unit)}</span></div>
          <div class="lines mid2">${linesHTML(s.lines)}</div></div>`;
      default:
        return "";
    }
  })();

  return `<section class="scene ${s.kind}" id="s${top / 1920}" data-i="${i}">
    <div class="bg"></div><div class="grain"></div>
    ${s.kind === "endcard" ? "" : brand()}
    ${body}
  </section>`;
}

const CSS = `
@import url("fonts/g.css");
:root{
  --green:#3A7D44; --green-dark:#2C5F34; --green-soft:#EDF3E8;
  --cream:#FAF6EF; --terra:#D96B4A; --amber:#E6A23C;
  --ink:#26302B; --muted:#68736C;
  --display:'Fraunces',Georgia,serif; --ui:'Nunito',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#111}
.scene{position:relative;display:none;width:1080px;height:1920px;overflow:hidden;
  background:var(--cream);color:var(--ink);font-family:var(--ui)}
.bg{position:absolute;inset:0;
  background:
    radial-gradient(900px 700px at 88% -6%, rgba(230,162,60,.16), transparent 62%),
    radial-gradient(760px 620px at -12% 104%, rgba(58,125,68,.13), transparent 60%),
    linear-gradient(180deg,#FBF8F2 0%, #FAF6EF 46%, #F6F1E7 100%);}
.grain{position:absolute;inset:0;opacity:.055;mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/></filter><rect width='180' height='180' filter='url(%23n)'/></svg>");}

.brand{position:absolute;left:88px;top:150px;display:flex;align-items:center;gap:18px;z-index:3}
.brand .mark{width:56px;height:56px;display:block}
.brand .word{font-family:var(--ui);font-weight:900;font-size:44px;letter-spacing:-.02em;color:var(--green-dark)}

.stack{position:absolute;left:88px;width:904px;z-index:2;display:flex;flex-direction:column}
.stack.hook{top:430px;gap:34px}
.stack.mid{top:50%;transform:translateY(-50%);gap:40px}
.stack.high{top:300px;gap:34px}
.stack.low{top:1180px;gap:30px}

.kicker{display:flex;align-items:center;gap:22px;font-size:64px;font-weight:800;
  letter-spacing:.10em;text-transform:uppercase;color:var(--green);line-height:1}
.kicker i{display:block;width:64px;height:8px;background:var(--terra);border-radius:4px;flex:none}

.num{font-family:var(--display);font-weight:600;font-size:250px;line-height:.86;
  letter-spacing:-.045em;color:var(--ink);font-variant-numeric:tabular-nums}
.lines{display:flex;flex-direction:column;gap:10px}
.ln{display:block;font-family:var(--ui);font-weight:800;font-size:76px;line-height:1.14;
  letter-spacing:-.015em;color:var(--ink);text-wrap:balance}
.lines.big .ln{font-family:var(--display);font-weight:600;font-size:118px;line-height:1.02;
  letter-spacing:-.03em}
.lines.mid2 .ln{font-family:var(--display);font-weight:600;font-size:96px;line-height:1.04;
  letter-spacing:-.025em}
.ln.green{color:var(--green)}
.ln.terra{color:var(--terra)}

.card{position:absolute;left:120px;top:820px;width:1000px;border-radius:30px;overflow:hidden;
  background:#fff;border:1px solid rgba(38,48,43,.10);
  box-shadow:0 50px 90px -40px rgba(38,48,43,.45), 0 2px 0 rgba(255,255,255,.6) inset;z-index:1}
.card img{width:100%;height:100%;object-fit:cover;object-position:center top;display:block}
.stack .lines.mid2{margin-top:0}

.cta .lines.big .ln{font-size:82px;line-height:1.1}
.pill{align-self:flex-start;margin-top:26px;display:inline-flex;align-items:center;gap:26px;
  background:var(--green);color:#fff;font-weight:800;font-size:64px;line-height:1;
  padding:34px 46px;border-radius:999px;letter-spacing:-.01em}
.pill .arw{font-size:64px}

.end{position:absolute;inset:0;background:var(--green);color:var(--cream);
  display:flex;flex-direction:column;align-items:flex-start;justify-content:center;
  padding:0 88px;gap:0}
.endmark{width:190px;height:190px;filter:brightness(0) saturate(100%) invert(97%) sepia(6%)
  saturate(300%) hue-rotate(340deg) brightness(103%);margin-bottom:44px}
.endword{font-family:var(--ui);font-weight:900;font-size:132px;letter-spacing:-.04em;line-height:1}
.endline{font-family:var(--display);font-weight:400;font-size:64px;margin-top:22px;opacity:.9}
.endcta{font-family:var(--display);font-weight:600;font-size:104px;margin-top:96px;line-height:1}
.endurl{font-family:var(--ui);font-weight:800;font-size:64px;margin-top:26px;opacity:.85}

.split{display:flex;align-items:center;gap:34px}
.snum{font-family:var(--display);font-weight:600;font-size:300px;line-height:.8;letter-spacing:-.05em}
.sarrow{width:150px;height:50px;flex:none;margin-top:10px}
.badge{margin-top:44px;align-self:flex-start;border:6px solid var(--terra);color:var(--terra);
  font-weight:900;font-size:64px;letter-spacing:.14em;padding:22px 40px;border-radius:999px;line-height:1}

.chip{align-self:flex-start;border:6px dashed var(--green);color:var(--green-dark);
  background:rgba(237,243,232,.7);font-weight:900;font-size:96px;letter-spacing:.06em;
  padding:34px 48px;border-radius:28px;line-height:1}

.counter{display:flex;align-items:baseline;gap:28px}
.cnum{font-family:var(--display);font-weight:600;font-size:320px;line-height:.8;letter-spacing:-.05em;color:var(--green)}
.cunit{font-family:var(--display);font-weight:600;font-size:110px;letter-spacing:-.02em}
`;

const TOTAL = Object.values(REELS).reduce((n, s) => n + s.length, 0);

const html = `<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<title>Sprossa KW46 – Storyboard</title><style>${CSS}
body{position:relative;width:1080px}
.scene:target{display:flex;flex-direction:column}
</style></head><body>
${(() => {
  let top = 0;
  return Object.entries(REELS)
    .map(([reel, scenes]) =>
      scenes
        .map((s, i) => {
          const h = sceneHTML(s, i, top).replace('class="scene', `data-reel="${reel}" class="scene`);
          top += 1920;
          return h;
        })
        .join("\n")
    )
    .join("\n");
})()}
</body></html>`;

fs.writeFileSync(HTML, html);

/* --------------------------------------------------------------- Rendern */

function findChromium() {
  const cache = path.join(os.homedir(), ".cache", "ms-playwright");
  for (const d of fs.readdirSync(cache).filter((x) => x.startsWith("chromium-")).sort().reverse()) {
    const p = path.join(cache, d, "chrome-linux", "chrome");
    if (fs.existsSync(p)) return p;
  }
  throw new Error("Chromium nicht gefunden");
}

const browser = await chromium.launch({ executablePath: findChromium(), args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto("file://" + HTML, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(900);

const manifest = [];
let top = 0;
for (const [reel, scenes] of Object.entries(REELS)) {
  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    const file = path.join(FRAMES, `${reel}-${String(i + 1).padStart(2, "0")}.png`);
    await page.goto("file://" + HTML + "#s" + top / 1920, { waitUntil: "load" });
    await page.waitForTimeout(120);
    await page.screenshot({ path: file });
    manifest.push({ reel, index: i + 1, file, dur: s.dur, motion: s.motion || "in" });
    top += 1920;
  }
  console.log(`  ${reel}: ${scenes.length} Frames`);
}
await browser.close();

fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2));
console.log(`Fertig: ${manifest.length} Frames → ${FRAMES}`);
