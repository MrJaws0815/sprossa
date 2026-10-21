"use client";
import Link from "next/link";

export default function RecipesPage() {
  const TOKEN_KEY = "sprossa_token";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100/api/v1";

  let recipes: any[] = [];

  async function loadRecipes() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/recipes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        recipes = await res.json();
      }
    } catch (e) {
      console.error("Fehler beim Laden der Rezepte", e);
    }
  }

  if (typeof window !== "undefined") {
    loadRecipes();
  }

  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">📖 Rezepte ({recipes.length})</h1>
        <button className="rounded-lg bg-sprossa-green px-4 py-2 text-sm text-white">
          + Neues Rezept
        </button>
      </div>

      {/* Rezept-Karten */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {recipes.length > 0
          ? recipes.map((r) => (
              <div key={r.id} className="rounded-xl border border-gray-200 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="font-semibold text-lg">{r.title}</h3>
                  {r.cook_once_eat_twice && (
                    <span className="rounded bg-sprossa-sage px-2 py-0.5 text-xs text-sprossa-dark">
                      Cook Once
                    </span>
                  )}
                </div>
                <div className="mb-2 flex gap-3 text-gray-500 text-xs">
                  <span>🍽 {r.servings} Port.</span>
                  {r.prep_time_minutes && <span>⏱ {r.prep_time_minutes + (r.cook_time_minutes || 0)} Min</span>}
                  <span>📊 {r.difficulty}</span>
                </div>
                <p className="mb-2 text-gray-600 text-sm">{r.description || ""}</p>
                <div className="flex flex-wrap gap-1">
                  {(r.tags || []).map((t: string) => (
                    <span
                      key={t}
                      className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))
          : (
            <div className="col-span-full rounded-lg border border-gray-200 p-8 text-center">
              <p className="text-gray-600">Keine Rezepte gefunden.</p>
            </div>
          )}
      </div>
    </section>
  );
}