#!/usr/bin/env node
/**
 * Sprossa KW46 – Layout-QA für die Reel-Frames.
 *
 * Prüft je Szene: Text innerhalb der IG-Safe-Area, Mindestschriftgröße 64 px,
 * kein horizontaler Überlauf, max. 2 Zeilen pro Overlay-Block.
 * Aufruf: node scripts/check_kw46.mjs
 */
import { chromium } from "playwright-core";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const OUT = "/home/mrjaws/monatsmenue/dist/reels/kw46";
const HTML = path.join(OUT, "storyboard.html");
const SAFE = { top: 120, bottom: 1700, left: 40, right: 1040 };

function findChromium() {
  const cache = path.join(os.homedir(), ".cache", "ms-playwright");
  for (const d of fs.readdirSync(cache).filter((x) => x.startsWith("chromium-")).sort().reverse()) {
    const p = path.join(cache, d, "chrome-linux", "chrome");
    if (fs.existsSync(p)) return p;
  }
  throw new Error("Chromium nicht gefunden");
}

const browser = await chromium.launch({ executablePath: findChromium(), args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto("file://" + HTML + "#s0", { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);

const n = await page.evaluate(() => document.querySelectorAll(".scene").length);
let problems = 0;

for (let i = 0; i < n; i++) {
  await page.goto("file://" + HTML + "#s" + i, { waitUntil: "load" });
  await page.waitForTimeout(80);
  const r = await page.evaluate((SAFE) => {
    const sc = document.querySelector(".scene:target");
    if (!sc) return { err: "kein :target" };
    const sr = sc.getBoundingClientRect();
    const out = [];
    const texts = [...sc.querySelectorAll(".ln, .num, .kicker, .pill, .chip, .badge, .snum, .cnum, .cunit, .endword, .endline, .endcta, .endurl")];
    for (const el of texts) {
      const b = el.getBoundingClientRect();
      const fs = parseFloat(getComputedStyle(el).fontSize);
      const rel = { x: b.left - sr.left, y: b.top - sr.top, w: b.width, h: b.height };
      if (fs < 64) out.push(`font ${fs.toFixed(0)}px < 64: "${el.textContent.trim().slice(0, 30)}"`);
      if (rel.x < SAFE.left - 1 || rel.x + rel.w > SAFE.right + 1)
        out.push(`horizontal: "${el.textContent.trim().slice(0, 24)}" x=${rel.x.toFixed(0)}..${(rel.x + rel.w).toFixed(0)}`);
      if (rel.y < SAFE.top - 1 || rel.y + rel.h > SAFE.bottom + 1)
        out.push(`vertikal: "${el.textContent.trim().slice(0, 24)}" y=${rel.y.toFixed(0)}..${(rel.y + rel.h).toFixed(0)}`);
    }
    // Text darf die Screen-Karte nicht überdecken
    const card = sc.querySelector(".card");
    if (card) {
      const c = card.getBoundingClientRect();
      for (const t of texts) {
        const b = t.getBoundingClientRect();
        const ox = Math.max(0, Math.min(b.right, c.right) - Math.max(b.left, c.left));
        const oy = Math.max(0, Math.min(b.bottom, c.bottom) - Math.max(b.top, c.top));
        if (ox > 2 && oy > 2)
          out.push(`überlappt Screen-Karte: "${t.textContent.trim().slice(0, 24)}"`);
      }
    }
    // Zeilen pro Overlay-Block
    const blocks = [...sc.querySelectorAll(".lines")];
    for (const bl of blocks) {
      const lines = bl.querySelectorAll(".ln").length;
      if (lines > 2) out.push(`overlay ${lines} Zeilen (max 2)`);
    }
    return { out, kind: sc.className };
  }, SAFE);
  if (r.err) { console.log(`#${i} FEHLER ${r.err}`); problems++; continue; }
  if (r.out.length) {
    problems += r.out.length;
    console.log(`#${i} ${r.kind}`);
    r.out.forEach((m) => console.log("   - " + m));
  }
}
await browser.close();
console.log(problems ? `\n${problems} Layout-Probleme` : "\nAlle Frames innerhalb der Safe-Area, Schrift >= 64px, max. 2 Zeilen.");
