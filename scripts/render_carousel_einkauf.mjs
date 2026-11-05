// Rendert die fünf Slides von carousel-einkauf.html als PNG (1080x1350).
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

const HTML = "/home/mrjaws/monatsmenue/dist/carousel/carousel-einkauf.html";
const OUT = "/home/mrjaws/monatsmenue/dist/carousel/out-einkauf";
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ headless: true, executablePath: findChromium(), args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });

await page.goto("file://" + HTML, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(600);

const slides = await page.$$("section.slide");
console.log(`Slides gefunden: ${slides.length}`);
for (let i = 0; i < slides.length; i++) {
  const num = String(i + 1).padStart(2, "0");
  const label = await slides[i].evaluate((el) => (el.className || "").replace("slide", "").trim().split(/\s+/)[0] || "slide");
  const file = path.join(OUT, `${num}-${label}.png`);
  await slides[i].screenshot({ path: file });
  const box = await slides[i].boundingBox();
  console.log(`  ${path.basename(file)} ${Math.round(box.width)}x${Math.round(box.height)} ${(fs.statSync(file).size / 1024).toFixed(0)} KB`);
}
await browser.close();
