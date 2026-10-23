"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authHeaders, getApiBase } from "../../lib/auth";
const dayNames = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"];

function currentMonthStr() {
  const n = new Date();
  return `${n.getMonth()+1}/${n.getFullYear()}`;
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

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const r = await fetch(`${getApiBase()}/plans`, { headers: authHeaders() });
      if (!r.ok) { setLoading(false); return; }
      const data: any[] = await r.json();
      setPlans(data);

      // Aktuellen Monat suchen, sonst den ersten Plan
      const now = `${new Date().getMonth()+1}/${new Date().getFullYear()}`;
      let target = data.find(p => `${p.month}/${p.year}` === now);
      if (!target && data.length > 0) target = data[0];
      if (target) await selectPlan(target);
    } catch(e) { setError("Fehler beim Laden der Pläne"); }
    setLoading(false);
  }

  async function selectPlan(p: any) {
    setActivePlanId(p.id);
    setActivePlanLabel(`${p.month}/${p.year}`);
    try {
      const r = await fetch(`${getApiBase()}/plans/${p.id}/weeks`, { headers: authHeaders() });
      const w = r.ok ? await r.json() : [];
      setWeeks(w);
      setSelectedWeek(0);
    } catch(e) { setError("Fehler beim Laden der Pläne"); }
  }

  async function generatePlan() {
    const now = new Date();
    const currentMonth = now.getMonth() + 1;
    const currentYear = now.getFullYear();
    
    // Prüfe ob schon ein Plan für diesen Monat existiert
    const existing = plans.find(p => p.month === currentMonth && p.year === currentYear);
    if (existing) {
      if (!confirm("Für " + currentMonth + "/" + currentYear + " existiert bereits ein Plan. Wirklich neu generieren?")) return;
    }
    
    setLoading(true);
    try {
      await fetch(`${getApiBase()}/plans/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ month: currentMonth, year: currentYear }),
      });
      await loadData();
    } catch(e) { setError("Fehler beim Laden der Pläne"); }
    setLoading(false);
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

      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold text-sprossa-ink">📅 {activePlanLabel}</h1>
        <button onClick={generatePlan} className="rounded-xl bg-sprossa-green px-4 py-2 font-bold text-white hover:bg-sprossa-dark">+ Neuen Plan generieren</button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Archiv: Letzte 12 Pläne */}
      {plans.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {plans.filter((_, i) => i < 12).map(p => {
            const label = `${p.month}/${p.year}`;
            const isCurrent = label === currentMonthStr();
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
      {weeks.length > selectedWeek && weeks[selectedWeek] && (
        <div className="rounded-xl border border-sprossa-ink/10 bg-white p-4">
          {(weeks[selectedWeek].meal_slots||[]).map((s:any) => (
            <div key={s.id} className="flex justify-between border-b border-sprossa-ink/10 py-2">
              <span className="font-medium text-sprossa-ink">{dayNames[s.day_of_week-1]||s.day_of_week}</span>
              <a href={"/dashboard/recipes/"+s.recipe_id} className="text-sm font-medium text-sprossa-green hover:underline hover:text-sprossa-dark transition-colors">
                {s.is_repeat ? "🔄 " : "🍽 "}{s.recipe_title}
              </a>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
