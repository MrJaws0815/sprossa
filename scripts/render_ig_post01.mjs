// Rendert dist/social/ig-post-01/carousel.html als PNG (2160x2700 @2x) und prueft,
// ob Text aus dem 1080x1350-Rahmen laeuft. Kein Upload, kein Netzwerk ausser lokalen Dateien.
import { chromium } from "playwright-core";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

function findChromium() {
  const cache = path.join(os.homedir(), ".cache", "ms-playwright");
  for (const d of fs.readdirSync(cache).filter((x) => x.startsWith("chromium-")).sort().reverse()) {
    const p = path.join(cache, d, "chrome-linux", "chrome");
    if (fs.existsSync(p)) return p;
  }
  throw new Error("kein Chromium gefunden");
}

const DIR = "/home/mrjaws/monatsmenue/dist/social/ig-post-01";
const HTML = path.join(DIR, "carousel.html");
const OUT = path.join(DIR, "png");
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath: findChromium(), args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });

const failed = [];
page.on("requestfailed", (r) => failed.push(`${r.url()} -> ${r.failure()?.errorText}`));
page.on("response", (r) => { if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`); });

await page.goto("file://" + HTML, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);

// Schriften wirklich geladen?
const fonts = await page.evaluate(() => {
  const probe = (font) => {
    const el = document.createElement("span");
    el.style.cssText = `position:absolute;visibility:hidden;font:${font};white-space:nowrap`;
    el.textContent = "Alle hungrig. Keine Antwort. 18 Uhr";
    document.body.appendChild(el);
    const w = el.getBoundingClientRect().width;
    el.remove();
    return Math.round(w * 100) / 100;
  };
  return {
    fraunces400: probe("400 100px Fraunces"),
    fraunces700: probe("700 100px Fraunces"),
    nunito600: probe("600 40px Nunito"),
    nunito800: probe("800 40px Nunito"),
    statuses: [...document.fonts].map((f) => `${f.family} ${f.weight} ${f.status}`),
  };
});

// Ueberlauf-Pruefung pro Slide und pro Textknoten
const check = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll("section.slide").forEach((slide, i) => {
    const cs = getComputedStyle(slide);
    const inner = slide.scrollHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    const overV = slide.scrollHeight > slide.clientHeight + 1;
    const bad = [];
    slide.querySelectorAll("h1,h2,p,div.row,div.note,.pill,.url,.hint,.stamp,.lead,.foot span").forEach((el) => {
      const r = el.getBoundingClientRect();
      const sr = slide.getBoundingClientRect();
      if (r.right > sr.right - 40 || r.left < sr.left + 40 || r.bottom > sr.bottom - 8) {
        bad.push(`${el.className || el.tagName} right=${Math.round(r.right - sr.left)} bottom=${Math.round(r.bottom - sr.top)}`);
      }
      if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflow !== "visible") {
        bad.push(`${el.className} h-overflow`);
      }
    });
    out.push({ slide: i + 1, height: slide.clientHeight, scrollHeight: slide.scrollHeight, overV, bad });
  });
  return out;
});

const slides = await page.$$("section.slide");
const names = ["01-cover", "02-szene", "03-plan", "04-woche", "05-statement", "06-cta"];
for (let i = 0; i < slides.length; i++) {
  const file = path.join(OUT, `${names[i] || String(i + 1)}.png`);
  await slides[i].screenshot({ path: file });
  const b = await slides[i].boundingBox();
  console.log(`  ${path.basename(file)} ${Math.round(b.width)}x${Math.round(b.height)} ${(fs.statSync(file).size / 1024).toFixed(0)} KB`);
}

console.log("SCHRIFTEN", JSON.stringify(fonts, null, 1));
console.log("LAYOUT", JSON.stringify(check, null, 1));
console.log("NETZWERK-FEHLER", failed.length ? failed : "keine");
await browser.close();
