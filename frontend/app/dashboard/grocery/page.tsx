"use client";
import Link from "next/link";

export default function GroceryPage() {
  const grouped = {
    Gemüse: ["Karotten (500 g)", "Kartoffeln (1 kg)", "Brokkoli (2 Stück)", "Zwiebeln (3 Stück)"],
    Fleisch: ["Hähnchenbrust (400 g)", "Hackfleisch (300 g)"],
    Milchprodukte: ["Sahne (200 ml)", "Butter (100 g)", "Milch (1 l)"],
    Getreide: ["Reis (500 g)", "Nudeln (500 g)", "Mehl (250 g)"],
    Gewürze: ["Salz", "Pfeffer", "Paprika edelsüß"],
  };

  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>
      <h1 className="mb-2 text-3xl font-bold">🛒 Einkaufsliste</h1>
      <p className="mb-6 text-gray-600 text-sm">
        Woche 1 · aus 7 Gerichten · für 4 Personen
      </p>

      {/* Nach Kategorien gruppiert */}
      {Object.entries(grouped).map(([kategorie, items]) => (
        <div key={kategorie} className="mb-4 rounded-lg border border-gray-200 p-4">
          <h2 className="mb-2 font-semibold text-lg">{kategorie}</h2>
          <ul className="space-y-1">
            {items.map((item) => (
              <li key={item} className="flex items-center gap-3">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-sm">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}

      <p className="mt-4 text-xs text-gray-400">
        ✅ Abgehakte Artikel werden beim nächsten Generieren zurückgesetzt.
      </p>
    </section>
  );
}