"use client";
import Link from "next/link";

export default function PlanPage() {
  const TOKEN_KEY = "sprossa_token";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100/api/v1";

  let plans: any[] = [];
  let selectedPlan: any = null;
  let weeks: any[] = [];
  let selectedWeek = 0;
  let currentMonth = new Date().getMonth() + 1;
  let currentYear = new Date().getFullYear();

  const dayNames = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];

  async function loadPlans() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/plans`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        plans = await res.json();
        if (plans.length > 0) {
          selectPlan(plans[0].id);
        }
      }
    } catch (e) {
      console.error("Fehler beim Laden der Pläne", e);
    }
  }

  async function selectPlan(planId: string) {
    const token = localStorage.getItem(TOKEN_KEY);
    selectedPlan = plans.find((p) => p.id === planId);

    try {
      const weeksRes = await fetch(`${API_BASE}/plans/${planId}/weeks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (weeksRes.ok) {
        weeks = await weeksRes.json();
      }
    } catch (e) {
      console.error("Fehler beim Laden der Wochen", e);
    }
  }

  async function generatePlan() {
    const token = localStorage.getItem(TOKEN_KEY);

    try {
      const res = await fetch(`${API_BASE}/plans/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ month: currentMonth, year: currentYear }),
      });
      if (res.ok) {
        loadPlans();
      }
    } catch (e) {
      console.error("Fehler bei Generierung", e);
    }
  }

  if (typeof window !== "undefined") {
    loadPlans();
  }

  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">
          📅 Plan {selectedPlan ? `${selectedPlan.month}/${selectedPlan.year}` : ""}
        </h1>
        <button
          onClick={generatePlan}
          className="rounded-lg bg-sprossa-green px-4 py-2 text-sm text-white"
        >
          + Neuen Plan generieren
        </button>
      </div>

      {/* Plan-Auswahl */}
      {plans.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {plans.map((p) => (
            <button
              key={p.id}
              onClick={() => selectPlan(p.id)}
              className={`rounded-lg px-3 py-1 text-sm ${
                selectedPlan?.id === p.id
                  ? "bg-sprossa-green text-white"
                  : "border border-gray-300 text-gray-700"
              }`}
            >
              {p.month}/{p.year} ({p.status})
            </button>
          ))}
        </div>
      )}

      {/* Wochen-Navigation */}
      {weeks.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {weeks.map((w, i) => (
            <button
              key={w.id || i}
              onClick={() => { selectedWeek = i; }}
              className={`rounded-lg px-4 py-2 text-sm ${
                selectedWeek === i
                  ? "bg-sprossa-green text-white"
                  : "border border-gray-300 text-gray-700"
              }`}
            >
              Woche {w.week_number}
            </button>
          ))}
        </div>
      )}

      {/* Wochen-Detail */}
      {weeks.length > selectedWeek && weeks[selectedWeek] && (
        <div className="rounded-lg border border-gray-200 p-4">
          <h2 className="mb-3 text-xl font-semibold">
            Woche {weeks[selectedWeek].week_number}
            {weeks[selectedWeek].start_date ? ` – ab ${weeks[selectedWeek].start_date}` : ""}
          </h2>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="pb-2 font-semibold">Tag</th>
                <th className="pb-2 font-semibold">Gericht</th>
                <th className="pb-2 font-semibold">Art</th>
                <th className="pb-2 font-semibold">Cook Once?</th>
              </tr>
            </thead>
            <tbody>
              {(weeks[selectedWeek].meal_slots || []).map((slot: any) => (
                <tr key={slot.id} className="border-b border-gray-100">
                  <td className="py-2 font-medium">
                    {dayNames[slot.day_of_week - 1] || `Tag ${slot.day_of_week}`}
                  </td>
                  <td className="py-2">🍽 Rezept</td>
                  <td className="py-2">{slot.meal_type}</td>
                  <td className="py-2">{slot.is_repeat ? "🔄 (Repeat)" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {weeks[selectedWeek].meal_slots?.filter?.((s: any) => s.is_repeat).length > 0 && (
            <p className="mt-3 text-xs text-gray-400">
              🔄 = Cook Once, Eat Twice – nur einmal kochen, am 2. Tag genießen.
            </p>
          )}
        </div>
      )}

      {/* Leerer State */}
      {plans.length === 0 && (
        <div className="rounded-lg border border-gray-200 p-8 text-center">
          <p className="mb-4 text-gray-600">Noch keine Pläne vorhanden.</p>
          <button
            onClick={generatePlan}
            className="rounded-lg bg-sprossa-green px-6 py-2 text-white"
          >
            📅 Ersten Plan generieren
          </button>
        </div>
      )}
    </section>
  );
}