#!/usr/bin/env node
/**
 * Sprossa – Reel-Standbilder aus dem HTML-Template rendern (1080×1920, 9:16).
 *
 * Das Template ist auf 330 px Vorschau gebaut. Für die Produktion skalieren wir
 * per CSS `zoom` auf 1080 px Breite – so skalieren auch Schrift und Abstände
 * mit, statt nur das Bild zu vergrößern (kein Weichzeichnen).
 *
 * Aufruf:
 *   node scripts/render_reels.mjs [template.html] [outdir]
 */

import { chromium } from "playwright-core";
import path from "node:path";
import fs from "node:fs";
import os from "node:os";

const VAULT = "/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa";
const DEFAULT_TEMPLATE = path.join(VAULT, "03 Marke & Design", "Sprossa Reel-Vorlagen Preview.html");
const DEFAULT_OUT = path.join("/home/mrjaws/monatsmenue", "dist", "reels");

const template = process.argv[2] || DEFAULT_TEMPLATE;
const outDir = process.argv[3] || DEFAULT_OUT;

function findChromium() {
  const cache = path.join(os.homedir(), ".cache", "ms-playwright");
  const dirs = fs.readdirSync(cache).filter((d) => d.startsWith("chromium-"));
  for (const d of dirs.sort().reverse()) {
    const p = path.join(cache, d, "chrome-linux", "chrome");
    if (fs.existsSync(p)) return p;
  }
  throw new Error("Chromium-Binary nicht gefunden");
}

if (!fs.existsSync(template)) {
  console.error(`Template nicht gefunden: ${template}`);
  process.exit(1);
}
fs.mkdirSync(outDir, { recursive: true });

const ZOOM = 1080 / 330; // 3.2727 – 330px Vorschau → 1080px Produktion

const browser = await chromium.launch({ executablePath: findChromium() });
const page = await browser.newPage({ viewport: { width: 1400, height: 2200 } });
await page.goto("file://" + encodeURI(template), { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(800);

await page.addStyleTag({
  content: `
    body { background: #ffffff !important; }
    .frames { gap: 80px !important; }
    /* Breite bleibt 330px – der Zoom (3.2727) hebt sie auf 1080px.
       Würde man zusätzlich width:1080px setzen, ergäbe sich 1080×3.27 = 3535px. */
    .reel {
      border-radius: 0 !important;
      box-shadow: none !important;
      zoom: ${ZOOM};
    }
    .label { font-size: 34px !important; }
  `,
});

const labels = await page.$$eval(".label", (els) => els.map((e) => e.textContent.trim()));
const reels = await page.$$(".reel");
console.log(`Gefunden: ${reels.length} Reels in ${path.basename(template)}`);

const slug = (s) =>
  s.toLowerCase().replace(/[^a-z0-9äöüß-]+/g, "-").replace(/^-+|-+$/g, "");

const saved = [];
for (let i = 0; i < reels.length; i++) {
  const label = labels[i] || `Reel ${i + 1}`;
  const name = `reel-${String(i + 1).padStart(2, "0")}-${slug(label)}.png`;
  const file = path.join(outDir, name);
  await reels[i].screenshot({ path: file });
  console.log(`  ✓ ${name} (${(fs.statSync(file).size / 1024).toFixed(0)} KB)`);
  saved.push(file);
}

await browser.close();

const { execSync } = await import("node:child_process");
for (const f of saved) {
  try {
    console.log("  " + execSync(`file "${f}"`, { encoding: "utf8" }).trim());
  } catch {}
}
console.log(`\nFertig: ${saved.length} Standbilder in ${outDir}`);
console.log("Hinweis: Das sind die Key-Frames. Für echte Reels daraus ein Video bauen");
console.log("(CapCut/Premiere: Bilder als Ebenen, Kamerafahrt + Schrift-Animation).");
