"use client";
import Link from "next/link";

export default function DashboardPage() {
  const TOKEN_KEY = "sprossa_token";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100/api/v1";

  // Statische Daten als Fallback (wenn kein Token)
  let stats = { recipes: 0, weeksPlanned: 0, groceryItems: 0 };
  let weeklyMeals: { day: string; meal: string }[] = [];
  let membersCount = 0;
  let planCount = 0;

  async function loadDashboard() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
      // Rezepte laden
      const recipesRes = await fetch(`${API_BASE}/recipes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (recipesRes.ok) {
        const recipes = await recipesRes.json();
        stats.recipes = recipes.length;
      }

      // Pläne laden
      const plansRes = await fetch(`${API_BASE}/plans`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (plansRes.ok) {
        const plans = await plansRes.json();
        planCount = plans.length;
        stats.weeksPlanned = plans.length * 4; // Annahme
      }

      // Einkaufslisten laden
      const groceryRes = await fetch(`${API_BASE}/grocery-lists`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (groceryRes.ok) {
        const lists = await groceryRes.json();
        stats.groceryItems = lists.reduce((acc: number, l: any) => acc + (l.items?.length || 0), 0);
      }

      // Letzten Plan laden für die Wochenvorschau
      const latestPlanRes = await fetch(`${API_BASE}/plans?limit=1`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (latestPlanRes.ok) {
        const plans = await latestPlanRes.json();
        if (plans.length > 0) {
          const weeksRes = await fetch(`${API_BASE}/plans/${plans[0].id}/weeks`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (weeksRes.ok) {
            const weeks = await weeksRes.json();
            if (weeks.length > 0) {
              const slots = weeks[0].meal_slots || [];
              const dayNames = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];
              weeklyMeals = slots.map((s: any) => ({
                day: dayNames[s.day_of_week - 1] || `Tag ${s.day_of_week}`,
                meal: s.meal_type === "dinner" ? "🍽 Rezept" : "🍳 Frühstück",
              }));
            }
          }
        }
      }
    } catch (e) {
      console.error("Fehler beim Laden des Dashboards", e);
    }
  }

  // Initial laden
  if (typeof window !== "undefined") {
    loadDashboard();
  }

  return (
    <section className="py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">📊 Dashboard</h1>
        <Link
          href="/dashboard/profile"
          className="rounded-lg border border-sprossa-green px-4 py-2 text-sm text-sprossa-green"
        >
          👤 Profil
        </Link>
      </div>

      {/* KPI-Karten */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <KpiCard label="Rezepte" value={stats.recipes} icon="📖" />
        <KpiCard label="Pläne" value={planCount} icon="📅" />
        <KpiCard label="Einkaufs-Items" value={stats.groceryItems} icon="🛒" />
      </div>

      {/* Nächste Woche */}
      <div className="mb-8 rounded-lg border border-gray-200 p-6">
        <h2 className="mb-4 text-xl font-semibold">📅 Wochenvorschau</h2>
        <div className="grid gap-3">
          {weeklyMeals.length > 0
            ? weeklyMeals.map((m) => (
                <div
                  key={m.day}
                  className="flex items-center justify-between border-b border-gray-100 pb-2"
                >
                  <span className="font-medium">{m.day}</span>
                  <span className="text-gray-500 text-sm">{m.meal}</span>
                </div>
              ))
            : ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"].map(
                (day) => (
                  <div
                    key={day}
                    className="flex items-center justify-between border-b border-gray-100 pb-2"
                  >
                    <span className="font-medium">{day}</span>
                    <span className="text-gray-500 text-sm">📅 Noch kein Plan</span>
                  </div>
                )
              )}
        </div>
      </div>

      {/* Links */}
      <div className="flex flex-wrap gap-4 justify-center">
        <Link
          href="/dashboard/plan"
          className="rounded-lg bg-sprossa-green px-6 py-2 text-white"
        >
          📅 Monatsplan ansehen
        </Link>
        <Link
          href="/dashboard/grocery"
          className="rounded-lg border border-sprossa-green px-6 py-2 text-sprossa-green"
        >
          🛒 Einkaufsliste
        </Link>
        <Link
          href="/dashboard/recipes"
          className="rounded-lg border border-gray-300 px-6 py-2 text-gray-700"
        >
          📖 Rezepte
        </Link>
      </div>
    </section>
  );
}

function KpiCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 p-5 text-center">
      <div className="mb-1 text-3xl">{icon}</div>
      <div className="mb-1 text-2xl font-bold">{value}</div>
      <div className="text-gray-500 text-sm">{label}</div>
    </div>
  );
}