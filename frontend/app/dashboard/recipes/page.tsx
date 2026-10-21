"use client";
import Link from "next/link";

export default function RecipesPage() {
  const recipes = [
    { title: "Nudeln mit Tomatensoße", servings: 4, time: "25 Min", difficulty: "einfach", tags: ["schnell", "vegetarisch"], twice: true },
    { title: "Kartoffel-Gratin", servings: 4, time: "45 Min", difficulty: "mittel", tags: ["vegetarisch"], twice: true },
    { title: "Hähnchen mit Reis", servings: 4, time: "30 Min", difficulty: "einfach", tags: ["proteinreich"], twice: false },
    { title: "Gemüse-Pfanne", servings: 4, time: "20 Min", difficulty: "einfach", tags: ["schnell", "vegetarisch"], twice: false },
  ];

  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">📖 Rezepte</h1>
        <button className="rounded-lg bg-sprossa-green px-4 py-2 text-sm text-white">
          + Neues Rezept
        </button>
      </div>

      {/* Rezept-Karte */}
      <div className="grid gap-4 md:grid-cols-2">
        {recipes.map((r) => (
          <div key={r.title} className="rounded-xl border border-gray-200 p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-semibold text-lg">{r.title}</h3>
              {r.twice && (
                <span className="rounded bg-sprossa-sage px-2 py-0.5 text-xs text-sprossa-dark">
                  Cook Once
                </span>
              )}
            </div>
            <div className="mb-2 flex gap-3 text-gray-500 text-xs">
              <span>🍽 {r.servings} Port.</span>
              <span>⏱ {r.time}</span>
              <span>📊 {r.difficulty}</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {r.tags.map((t) => (
                <span
                  key={t}
                  className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}