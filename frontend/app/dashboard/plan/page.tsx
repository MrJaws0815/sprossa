"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import SprossMark from "../../SprossMark";
import { authHeaders, getApiBase } from "../../lib/auth";
import { germanMonthYear } from "../../lib/dates";
const dayNames = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"];

/**
 * Backend akzeptiert nur aktuellen und naechsten Monat (sonst 422).
 * Jahresueberlauf: im Dezember ist der naechste Monat Januar des Folgejahres.
 */
function allowedMonths(): { month: number; year: number }[] {
  const now = new Date();
  const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return [
    { month: now.getMonth() + 1, year: now.getFullYear() },
    { month: next.getMonth() + 1, year: next.getFullYear() },
  ];
}

/** Portionsskalierung: total_portions / recipe.servings, deutsches Komma. */
function scaledServingsLabel(slot: any): string {
  const multiplier = Number(slot?.servings_multiplier ?? 1);
  const base = Number(slot?.recipe_servings);
  // Toleranz gegen Float-Rauschen (1.0000000001 soll nicht als Skalierung gelten)
  if (!Number.isFinite(multiplier) || Math.abs(multiplier - 1) < 1e-6) return "";
  if (!Number.isFinite(base)) return "";
  const scaled = base * multiplier;
  if (!Number.isFinite(scaled)) return "";
  return `angepasst: ${scaled.toFixed(1).replace(".", ",")} Portionen`;
}

export default function PlanPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<any[]>([]);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);
  const [activePlanLabel, setActivePlanLabel] = useState("–");
  const [weeks, setWeeks] = useState<any[]>([]);
  const [selectedWeek, setSelectedWeek] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [swappingSlotId, setSwappingSlotId] = useState<string | null>(null);
  const [swapError, setSwapError] = useState("");
  const monthOptions = allowedMonths();
  const [genMonth, setGenMonth] = useState(monthOptions[0].month);
  const [genYear, setGenYear] = useState(monthOptions[0].year);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData(preferred?: { month: number; year: number }) {
    try {
      const r = await fetch(`${getApiBase()}/plans`, { headers: authHeaders() });
      if (!r.ok) { setLoading(false); return; }
      const data: any[] = await r.json();
      setPlans(data);

      // Bevorzugt: explizit angeforderter Plan (z. B. gerade generiert),
      // dann aktueller Monat, sonst der erste Plan.
      const now = new Date();
      const currentMonth = now.getMonth() + 1;
      const currentYear = now.getFullYear();
      let target = preferred
        ? data.find(p => p.month === preferred.month && p.year === preferred.year)
        : undefined;
      if (!target) target = data.find(p => p.month === currentMonth && p.year === currentYear);
      if (!target && data.length > 0) target = data[0];
      if (target) await selectPlan(target);
    } catch(e) { setError("Fehler beim Laden der Pläne"); }
    setLoading(false);
  }

  async function selectPlan(p: any) {
    setActivePlanId(p.id);
    setActivePlanLabel(germanMonthYear(p.month, p.year));
    try {
      const r = await fetch(`${getApiBase()}/plans/${p.id}/weeks`, { headers: authHeaders() });
      const w = r.ok ? await r.json() : [];
      setWeeks(w);
      setSelectedWeek(0);
    } catch(e) { setError("Fehler beim Laden der Pläne"); }
  }

  async function generatePlan() {
    // Prüfe ob schon ein Plan für die Auswahl existiert (Backend macht Upsert)
    const existing = plans.find(p => p.month === genMonth && p.year === genYear);
    const label = germanMonthYear(genMonth, genYear);
    const action = existing ? "aktualisiert" : "generiert";
    if (existing) {
      if (!confirm(`Für ${label} existiert bereits ein Plan. Er wird beim Fortfahren aktualisiert. Fortfahren?`)) return;
    } else {
      if (!confirm(`Neuen Plan für ${label} generieren?`)) return;
    }

    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${getApiBase()}/plans/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ month: genMonth, year: genYear }),
      });
      if (!res.ok) {
        // 422 (Monats-Scope) / 400 (keine saisonal passenden Rezepte):
        // detail-Text der API direkt anzeigen statt generischem Fehler.
        const err = await res.json().catch(() => ({} as any));
        const detail = Array.isArray(err?.detail)
          ? err.detail.map((d: any) => d?.msg ?? String(d)).join("; ")
          : err?.detail;
        setError(
          detail
            ? `Plan für ${label} konnte nicht ${action} werden: ${detail}`
            : `Plan für ${label} konnte nicht ${action} werden.`
        );
        setLoading(false);
        return;
      }
      await loadData({ month: genMonth, year: genYear });
    } catch(e) { setError("Fehler beim Laden der Pläne"); }
    setLoading(false);
  }

  async function handleSwap(slotId: string) {
    if (!activePlanId) return;
    setSwappingSlotId(slotId);
    setSwapError("");
    try {
      const r = await fetch(`${getApiBase()}/plans/${activePlanId}/slots/${slotId}/swap`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({}),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        setSwapError(err.detail || "Tauschen fehlgeschlagen. Bitte erneut versuchen.");
        return;
      }
      const updated = await r.json();
      setWeeks(prev => prev.map(w => ({
        ...w,
        meal_slots: (w.meal_slots || []).map((s: any) =>
          s.id === updated.id
            ? {
                ...s,
                recipe_id: updated.recipe?.id ?? updated.recipe_id ?? s.recipe_id,
                recipe_title: updated.recipe?.title ?? updated.recipe_title ?? s.recipe_title,
                servings_multiplier: updated.servings_multiplier ?? s.servings_multiplier,
                recipe_servings: updated.recipe_servings ?? s.recipe_servings,
              }
            : s
        ),
      })));
    } catch (e) {
      setSwapError("Netzwerkfehler beim Tauschen.");
    } finally {
      setSwappingSlotId(null);
    }
  }

  function currentCW() { const d=new Date(); const s=d.getTime(); const y=d.getFullYear(); const jan1=new Date(y,0,1); const days=Math.floor((s-jan1.getTime())/86400000); return Math.ceil((days+jan1.getDay()+1)/7); }

  if (loading) return (
    <section className="py-8">
      <div className="p-8 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-sprossa-muted/10 rounded-xl h-24" />
        ))}
      </div>
    </section>
  );

  return (
    <section className="py-8">
      <div className="mb-4"><Link href="/dashboard" className="text-sprossa-green text-sm">← Dashboard</Link></div>

      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h1 className="flex items-center gap-2 font-display text-3xl font-bold text-sprossa-ink"><SprossMark size={26} color="#3A7D44" /><span>{activePlanLabel}</span></h1>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1 text-sm text-sprossa-muted">
            <span className="sr-only">Monat</span>
            <select
              value={`${genYear}-${String(genMonth).padStart(2, "0")}`}
              onChange={(e) => {
                const [year, month] = e.target.value.split("-").map(Number);
                setGenYear(year);
                setGenMonth(month);
              }}
              className="rounded-xl border border-sprossa-muted/20 bg-white px-3 py-2 text-sm text-sprossa-ink"
            >
              {monthOptions.map((o) => (
                <option
                  key={`${o.year}-${o.month}`}
                  value={`${o.year}-${String(o.month).padStart(2, "0")}`}
                >
                  {germanMonthYear(o.month, o.year)}
                </option>
              ))}
            </select>
          </label>
          <button onClick={generatePlan} className="rounded-xl bg-sprossa-green px-4 py-2 font-bold text-white hover:bg-sprossa-dark">
            {plans.some(p => p.month === genMonth && p.year === genYear)
              ? `${germanMonthYear(genMonth, genYear)} aktualisieren`
              : `Plan für ${germanMonthYear(genMonth, genYear)} generieren`}
          </button>
        </div>
      </div>
      {plans.some(p => p.month === genMonth && p.year === genYear) && (
        <p className="mb-4 text-sm text-sprossa-muted">
          Für {germanMonthYear(genMonth, genYear)} existiert bereits ein Plan – er wird aktualisiert.
        </p>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Archiv: Letzte 12 Pläne */}
      {plans.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {plans.filter((_, i) => i < 12).map(p => {
            const label = germanMonthYear(p.month, p.year);
            const now = new Date();
            const isCurrent = p.month === now.getMonth() + 1 && p.year === now.getFullYear();
            return (
              <button key={p.id} onClick={() => selectPlan(p)}
                className={`rounded-lg px-3 py-1 text-sm font-bold ${activePlanId===p.id ? "bg-sprossa-green text-white" : isCurrent ? "bg-sprossa-dark text-white" : "border border-sprossa-muted/30 text-sprossa-ink"}`}>
                {label}{isCurrent ? " ★" : ""}
              </button>
            );
          })}
        </div>
      )}

      {/* Keine Pläne */}
      {plans.length === 0 && (
        <div className="rounded-xl border border-sprossa-ink/10 bg-white p-8 text-center">
          <p className="mb-4 text-sprossa-muted">Noch keine Pläne.</p>
          <button onClick={generatePlan} className="rounded-xl bg-sprossa-green px-6 py-2 font-bold text-white">📅 Ersten Plan generieren</button>
        </div>
      )}

      {/* Wochen */}
      {weeks.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {weeks.map((w,i) => (
            <button key={i} onClick={()=>setSelectedWeek(i)}
              className={`rounded-lg px-4 py-2 text-sm ${selectedWeek===i?"bg-sprossa-green text-white":"border border-sprossa-muted/30 text-sprossa-ink"}`}>
              KW {w.cw || w.week_number}
            </button>
          ))}
        </div>
      )}

      {/* Slots */}
      {swapError && (
        <div className="mb-3 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {swapError}
        </div>
      )}
      {weeks.length > selectedWeek && weeks[selectedWeek] && (
        <div className="rounded-xl border border-sprossa-ink/10 bg-white p-4">
          {(weeks[selectedWeek].meal_slots||[]).map((s:any) => {
            const scaled = scaledServingsLabel(s);
            return (
              <div key={s.id} className="flex justify-between items-center border-b border-sprossa-ink/10 py-2">
                <span className="font-medium text-sprossa-ink">{dayNames[s.day_of_week-1]||s.day_of_week}</span>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <a href={"/dashboard/recipes/"+s.recipe_id+"?multiplier="+(s.servings_multiplier ?? 1)} className="text-sm font-medium text-sprossa-green hover:underline hover:text-sprossa-dark transition-colors">
                    {s.is_repeat ? "🔄 " : "🍽 "}{s.recipe_title || "Rezept wird geladen…"}
                  </a>
                  {scaled && (
                    <span className="rounded-md bg-sprossa-sage px-2 py-0.5 text-xs font-medium text-sprossa-dark">
                      {scaled}
                    </span>
                  )}
                  <button
                    onClick={() => handleSwap(s.id)}
                    disabled={swappingSlotId === s.id}
                    className="rounded-lg border border-sprossa-green px-2 py-1 text-xs font-bold text-sprossa-green hover:bg-sprossa-green hover:text-white disabled:opacity-50 transition-colors"
                  >
                    {swappingSlotId === s.id ? "…" : "Tauschen"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
