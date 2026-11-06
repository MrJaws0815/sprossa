// Rendert ein Social-HTML (post.html) seitenweise zu PNG und prueft dabei
// Layout, Raender, Schriften und Netzwerkfehler.
//
// Aufruf: node scripts/render_social_post.mjs <ordner>
// Erwartet <ordner>/post.html, schreibt <ordner>/png/<data-name>.png (2x).
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

const dir = process.argv[2];
if (!dir) throw new Error("Aufruf: node scripts/render_social_post.mjs <ordner>");
const DIR = path.resolve(dir);
const HTML = path.join(DIR, "post.html");
const OUT = path.join(DIR, "png");
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: findChromium(),
  args: ["--no-sandbox"],
});
const page = await browser.newPage({
  viewport: { width: 1080, height: 1350 },
  deviceScaleFactor: 2,
});

const failed = [];
page.on("requestfailed", (r) => failed.push(`${r.url()} -> ${r.failure()?.errorText}`));
page.on("response", (r) => {
  if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`);
});

await page.goto("file://" + HTML, { waitUntil: "load" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);

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
    loaded: [...document.fonts].filter((f) => f.status === "loaded").length,
  };
});

const check = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll("section.slide").forEach((slide, i) => {
    const cs = getComputedStyle(slide);
    const overV = slide.scrollHeight > slide.clientHeight + 1;
    const bad = [];
    slide
      .querySelectorAll("h1,h2,h3,p,li,div.row,div.note,.pill,.url,.hint,.stamp,.lead,.foot span,td,th")
      .forEach((el) => {
        const r = el.getBoundingClientRect();
        const sr = slide.getBoundingClientRect();
        if (r.right > sr.right - 40 || r.left < sr.left + 40 || r.bottom > sr.bottom - 8) {
          bad.push(`${el.className || el.tagName} right=${Math.round(r.right - sr.left)} bottom=${Math.round(r.bottom - sr.top)}`);
        }
        if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflow !== "visible") {
          bad.push(`${el.className || el.tagName} h-overflow`);
        }
      });
    out.push({ slide: i + 1, w: slide.clientWidth, h: slide.clientHeight, scrollHeight: slide.scrollHeight, overV, bad });
  });
  return out;
});

const slides = await page.$$("section.slide");
let problems = 0;
for (let i = 0; i < slides.length; i++) {
  const name = (await slides[i].getAttribute("data-name")) || String(i + 1).padStart(2, "0");
  const file = path.join(OUT, `${name}.png`);
  await slides[i].screenshot({ path: file });
  const b = await slides[i].boundingBox();
  const meta = check[i];
  if (meta.overV || meta.bad.length) problems++;
  console.log(
    `  ${path.basename(file)} ${Math.round(b.width / 2)}x${Math.round(b.height / 2)} ` +
      `${(fs.statSync(file).size / 1024).toFixed(0)}KB` +
      (meta.overV ? "  UEBERLAUF-V" : "") +
      (meta.bad.length ? `  PROBLEME: ${meta.bad.join("; ")}` : "  ok")
  );
}

if (fonts.fraunces400 === fonts.fraunces700) {
  console.log("  ! Fraunces 400 und 700 messen gleich breit - Schrift evtl. nicht geladen");
  problems++;
}
if (failed.length) {
  console.log("  ! Netzwerkfehler:", failed);
  problems++;
}

console.log(`\nFERTIG ${slides.length} Slides, ${problems} mit Problemen`);
await browser.close();
process.exit(problems ? 1 : 0);
