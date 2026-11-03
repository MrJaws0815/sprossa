// Deutsche Monatsnamen + ISO-Kalenderwoche (ohne externe Abhängigkeiten).

export const GERMAN_MONTHS = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
] as const;

/** 1-basiert: germanMonth(10) -> "Oktober" */
export function germanMonth(month: number): string {
  return GERMAN_MONTHS[month - 1] ?? String(month);
}

/** "Oktober 2026" */
export function germanMonthYear(month: number, year: number): string {
  return `${germanMonth(month)} ${year}`;
}

/** ISO-8601 Kalenderwoche (Montag als Wochenstart, KW 1 enthält den 4. Januar). */
export function isoWeek(date: Date = new Date()): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7; // Sonntag = 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

/** "Oktober 2026" für einen Monatsplan, mit Fallback auf month/year. */
export function planLabel(p: { month?: number | null; year?: number | null }): string {
  if (p?.month && p?.year) return germanMonthYear(p.month, p.year);
  return "–";
}
