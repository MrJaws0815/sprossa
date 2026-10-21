"use client";
import Link from "next/link";

export default function DashboardPage() {
  const stats = {
    households: 1,
    members: 4,
    recipes: 12,
    weeksPlanned: 4,
    mealsThisWeek: 7,
    groceryItems: 23,
  };

  return (
    <section className="py-8">
      <h1 className="mb-6 text-3xl font-bold">Dashboard</h1>

      {/* KPI-Karten */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <KpiCard label="Familien" value={stats.households} icon="🏠" />
        <KpiCard label="Mitglieder" value={stats.members} icon="👨‍👩‍👧‍👦" />
        <KpiCard label="Rezepte" value={stats.recipes} icon="📖" />
      </div>

      {/* Nächste Woche */}
      <div className="mb-8 rounded-lg border border-gray-200 p-6">
        <h2 className="mb-4 text-xl font-semibold">Diese Woche</h2>
        <div className="grid gap-3">
          {["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"].map(
            (day, i) => (
              <div
                key={day}
                className="flex items-center justify-between border-b border-gray-100 pb-2"
              >
                <span className="font-medium">{day}</span>
                <span className="text-gray-500 text-sm">
                  {i < 5 ? "🌿 Nudeln mit Tomatensoße" : i === 5 ? "🍗 Hähnchen mit Reis" : "🥘 Reste-Essen"}
                </span>
              </div>
            )
          )}
        </div>
      </div>

      {/* Wochenplan + Einkaufsliste Links */}
      <div className="flex gap-4 justify-center">
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