// Frischer Screenshot der Einkaufsliste für Carousel 2.
// Vorher prüfen: kein Emoji in der H1, Mengen im deutschen Format.
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

const BASE = "http://192.168.178.188:3100";
const OUT = "/home/mrjaws/monatsmenue/dist/carousel/screens/grocery-fresh.png";

const browser = await chromium.launch({ headless: true, executablePath: findChromium(), args: ["--no-sandbox"] });
const ctx = await browser.newContext({ viewport: { width: 984, height: 931 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(1000);
await page.fill('input[type="email"]', "demo@sprossa.de");
await page.fill('input[type="password"]', "demo1234");
await page.click('button[type="submit"]');
await page.waitForTimeout(4000);

await page.goto(`${BASE}/dashboard/grocery`, { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(2500);

const info = await page.evaluate(() => {
  const h1 = document.querySelector("h1");
  const text = document.body.innerText;
  return {
    url: location.pathname,
    h1: h1?.innerText || "",
    hasEmoji: /[\u{1F300}-\u{1FAFF}]/u.test(h1?.innerText || ""),
    hasComma: /\d,\d/.test(text),
    hasDotDecimal: /\d\.\d{1,2}\s*(Stück|g|kg|ml|l|Bund|Dose)/.test(text),
    items: document.querySelectorAll('input[type="checkbox"]').length,
    sample: text.split("\n").filter((l) => /\(/.test(l)).slice(0, 4),
  };
});

await page.screenshot({ path: OUT });
const stat = fs.statSync(OUT);
console.log(JSON.stringify({ ...info, file: OUT, bytes: stat.size }, null, 1));
await browser.close();
