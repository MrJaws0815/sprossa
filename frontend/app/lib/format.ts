/**
 * Mengen-Anzeige für Einkaufslisten und Rezepte.
 *
 * Problem vorher: rohe Floats aus der DB wurden per `toFixed(2)` gezeigt –
 * "1.85 Stück Avocado", "0.62 Ei", "1.00 Bund Petersilie". Im Supermarkt
 * unbrauchbar und ein direkter Vertrauensbruch bei einer App, die behauptet,
 * Einkaufen einfacher zu machen.
 *
 * Regeln (de-DE, Komma als Dezimaltrenner):
 *  - Zählbare Einheiten (Stück, Bund, Dose, Packung, Scheibe, Zehe, Prise):
 *    auf 0,5 runden, ganze Zahlen ohne Nachkommastelle. Unter 0,5 → "0,5"
 *    (halbe Packung ist kaufbar, ein Viertel Ei nicht).
 *  - Gramm / Milliliter: bis 100 → 5er-Schritte, darüber 10er-Schritte.
 *  - Kilogramm / Liter: eine Nachkommastelle, ganze Werte ohne Komma.
 *  - Alles andere: eine Nachkommastelle.
 */

const COUNT_UNITS = new Set([
  "stück", "stk", "st", "bund", "dose", "dosen", "packung", "packungen",
  "scheibe", "scheiben", "zehe", "zehen", "prise", "prisen", "kopf", "köpfe",
  "becher", "glas", "gläser", "beutel", "päckchen", "kugel", "kugeln",
  "ei", "eier", "zwiebel", "zwiebeln", "kartoffel", "kartoffeln", "tomate",
  "tomaten", "gurke", "gurken", "paprika", "karotte", "karotten", "möhre",
  "möhren", "zitrone", "zitronen", "limette", "limetten", "blatt", "blätter",
  "stange", "stangen", "stängel", "salat", "kohlrabi", "zucchini", "aubergine",
  "avocado", "avocados", "banane", "bananen", "apfel", "äpfel", "birne",
  "birnen", "orange", "orangen", "lauch", "porree", "sellerie", "ingwer",
]);

const GRAM_UNITS = new Set(["g", "gramm", "ml", "milliliter"]);
const KILO_UNITS = new Set(["kg", "kilogramm", "l", "liter"]);

function normalizeUnit(unit: string | null | undefined): string {
  return (unit ?? "").trim().toLowerCase();
}

/** Kaufmännisch runden (halbe Werte auf, wie im Supermarkt üblich). */
function roundTo(value: number, step: number): number {
  if (step <= 0) return value;
  return Math.round(value / step) * step;
}

/** Zahl als deutscher String: Komma, keine unnötigen Nullen. */
function deNumber(value: number, maxDecimals: number): string {
  const rounded = Number(value.toFixed(maxDecimals));
  if (Number.isInteger(rounded)) return String(rounded);
  return rounded.toFixed(maxDecimals).replace(/0+$/, "").replace(/\.$/, "").replace(".", ",");
}

export function formatQuantity(
  quantity: number | string | null | undefined,
  unit: string | null | undefined,
): string {
  const raw = typeof quantity === "string" ? Number.parseFloat(quantity) : quantity;
  if (raw == null || Number.isNaN(raw)) return "—";

  const u = normalizeUnit(unit);
  let value: number;
  let decimals: number;

  if (COUNT_UNITS.has(u)) {
    value = Math.max(0.5, roundTo(raw, 0.5));
    decimals = 1;
  } else if (GRAM_UNITS.has(u)) {
    value = raw < 100 ? Math.max(5, roundTo(raw, 5)) : Math.max(10, roundTo(raw, 10));
    decimals = 0;
  } else if (KILO_UNITS.has(u)) {
    value = Math.max(0.1, roundTo(raw, 0.1));
    decimals = 1;
  } else {
    value = roundTo(raw, 0.1);
    decimals = 1;
  }

  const number = deNumber(value, decimals);
  const unitLabel = (unit ?? "").trim();
  return unitLabel ? `${number} ${unitLabel}` : number;
}

/** Kurzform ohne Einheit – für Stellen, wo die Einheit in einer eigenen Spalte steht. */
export function formatQuantityValue(
  quantity: number | string | null | undefined,
  unit: string | null | undefined,
): string {
  const full = formatQuantity(quantity, unit);
  const unitLabel = (unit ?? "").trim();
  return unitLabel && full.endsWith(unitLabel)
    ? full.slice(0, full.length - unitLabel.length).trim()
    : full;
}
