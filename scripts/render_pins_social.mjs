// Rendert die neuen Pinterest-Pins (1000x1500) aus dist/social/pin-neu-01/pins.html.
// Prüft: EXAKTE Maße, kein Overflow, Schriften geladen, Text in der Safe Zone.
import { chromium } from "playwright-core";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const HTML_DIR = "/home/mrjaws/monatsmenue/dist/social/pin-neu-01";
const HTML = path.join(HTML_DIR, "pins.html");

function findChromium() {
  const cache = path.join(os.homedir(), ".cache", "ms-playwright");
  for (const d of fs.readdirSync(cache).filter((x) => x.startsWith("chromium-")).sort().reverse()) {
    const p = path.join(cache, d, "chrome-linux", "chrome");
    if (fs.existsSync(p)) return p;
  }
  throw new Error("kein Chromium gefunden");
}

const browser = await chromium.launch({ headless: true, executablePath: findChromium(), args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1100, height: 1600 }, deviceScaleFactor: 1 });
await page.goto("file://" + HTML, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(800);

const fonts = await page.evaluate(() => ({
  fraunces: document.fonts.check("500 104px Fraunces"),
  nunito: document.fonts.check("700 33px Nunito"),
}));
console.log("Schriften geladen:", JSON.stringify(fonts));
if (!fonts.fraunces || !fonts.nunito) throw new Error("CI-Schriften fehlen – Abbruch");

const pins = await page.$$(".pin");
console.log(`Pins gefunden: ${pins.length}`);
let fails = 0;
for (const pin of pins) {
  const name = await pin.evaluate((el) => el.dataset.name);
  const info = await pin.evaluate((el) => {
    const box = el.getBoundingClientRect();
    const kids = [...el.querySelectorAll("*")].map((n) => {
      const r = n.getBoundingClientRect();
      return { t: n.textContent.trim().slice(0, 40), l: r.left - box.left, r: box.right - r.right, b: box.bottom - r.bottom };
    });
    const minL = Math.min(...kids.map((k) => k.l));
    const minR = Math.min(...kids.map((k) => k.r));
    const minB = Math.min(...kids.map((k) => k.b));
    return {
      w: Math.round(box.width), h: Math.round(box.height),
      scrollH: el.scrollHeight, scrollW: el.scrollWidth,
      minLeft: Math.round(minL), minRight: Math.round(minR), minBottom: Math.round(minB),
    };
  });
  const ok = info.w === 1000 && info.h === 1500 && info.scrollH <= 1500 && info.scrollW <= 1000 && info.minBottom >= 60;
  if (!ok) fails++;
  console.log(`  ${name}: ${info.w}x${info.h} scroll=${info.scrollW}x${info.scrollH} Rand L${info.minLeft}/R${info.minRight}/U${info.minBottom} -> ${ok ? "OK" : "PRÜFEN"}`);
  const file = path.join(HTML_DIR, `${name}.png`);
  await pin.screenshot({ path: file });
  console.log(`    → ${path.basename(file)} ${(fs.statSync(file).size / 1024).toFixed(0)} KB`);
}
await browser.close();
if (fails) { console.error(`${fails} Pin(s) außerhalb der Vorgaben`); process.exit(1); }
console.log("Fertig.");
