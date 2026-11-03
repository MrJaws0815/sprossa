#!/usr/bin/env node
/**
 * Sprossa – Pinterest-Pins aus dem HTML-Template rendern.
 *
 * Warum: Das Template zeigt die Pins in einer Vorschau auf 40 % (400×600 px).
 * Für Pinterest brauchen wir echte 1000×1500 px. Dieses Skript hebt die
 * Skalierung auf, wartet auf die Schriften (Fraunces/Nunito von Google Fonts)
 * und speichert jeden Pin als PNG.
 *
 * Aufruf:
 *   node scripts/render_pins.mjs [template.html] [outdir]
 * Default:
 *   template = 03 Marke & Design/Sprossa - Pinterest-Pin-Vorlagen.html (im Vault)
 *   outdir   = dist/pins
 *
 * Voraussetzung: playwright-core (im Projekt installiert) + Chromium-Cache.
 */

import { chromium } from "playwright-core";
import path from "node:path";
import fs from "node:fs";
import os from "node:os";

const VAULT = "/home/mrjaws/Documents/Obsidian/Main Vault/Sprossa";
const DEFAULT_TEMPLATE = path.join(VAULT, "03 Marke & Design", "Sprossa - Pinterest-Pin-Vorlagen.html");
const DEFAULT_OUT = path.join("/home/mrjaws/monatsmenue", "dist", "pins");

const template = process.argv[2] || DEFAULT_TEMPLATE;
const outDir = process.argv[3] || DEFAULT_OUT;

// Chromium aus dem Playwright-Cache (kein Download nötig)
function findChromium() {
  const cache = path.join(os.homedir(), ".cache", "ms-playwright");
  if (!fs.existsSync(cache)) throw new Error(`Kein Playwright-Cache: ${cache}`);
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

const browser = await chromium.launch({ executablePath: findChromium() });
const page = await browser.newPage({ viewport: { width: 1400, height: 1200 } });

await page.goto("file://" + encodeURI(template), { waitUntil: "networkidle" });
// Schriften laden (Fraunces/Nunito kommen von Google Fonts)
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(800);

// Skalierung aufheben: Pin in voller Größe rendern
await page.addStyleTag({
  content: `
    .pin-wrapper { width: 1000px !important; height: 1500px !important;
                   overflow: visible !important; border-radius: 0 !important;
                   box-shadow: none !important; }
    .pin { transform: none !important; }
    body { background: #ffffff !important; }
  `,
});

const labels = await page.$$eval(".pin-label", (els) => els.map((e) => e.textContent.trim()));
const pins = await page.$$(".pin");

console.log(`Gefunden: ${pins.length} Pins in ${path.basename(template)}`);

const slug = (s) =>
  s
    .toLowerCase()
    .replace(/·/g, "-")
    .replace(/[^a-z0-9äöüß-]+/g, "-")
    .replace(/^-+|-+$/g, "");

const saved = [];
for (let i = 0; i < pins.length; i++) {
  const label = labels[i] || `Pin ${i + 1}`;
  const name = `pin-${String(i + 1).padStart(2, "0")}-${slug(label)}.png`;
  const file = path.join(outDir, name);
  await pins[i].screenshot({ path: file });
  const size = fs.statSync(file).size;
  console.log(`  ✓ ${name} (${(size / 1024).toFixed(0)} KB)`);
  saved.push({ file, label, size });
}

await browser.close();

// Kontrolle: Maße prüfen
const { execSync } = await import("node:child_process");
for (const s of saved) {
  try {
    const out = execSync(`file "${s.file}"`, { encoding: "utf8" });
    console.log("  " + out.trim());
  } catch {}
}
console.log(`\nFertig: ${saved.length} PNGs in ${outDir}`);
