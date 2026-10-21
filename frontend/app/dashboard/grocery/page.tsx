"use client";
import Link from "next/link";

export default function GroceryPage() {
  const TOKEN_KEY = "sprossa_token";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100/api/v1";

  let groceryLists: any[] = [];
  let selectedList: any = null;
  let grouped: Record<string, any[]> = {};

  async function loadGrocery() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/grocery-lists`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        groceryLists = await res.json();
        if (groceryLists.length > 0) {
          selectList(groceryLists[0].id);
        }
      }
    } catch (e) {
      console.error("Fehler beim Laden der Einkaufslisten", e);
    }
  }

  async function selectList(listId: string) {
    const token = localStorage.getItem(TOKEN_KEY);
    selectedList = groceryLists.find((l) => l.id === listId);

    try {
      const res = await fetch(`${API_BASE}/grocery-lists/${listId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const full = await res.json();
        // Nach Kategorie gruppieren
        grouped = {};
        for (const item of full.items || []) {
          const cat = item.category || "other";
          if (!grouped[cat]) grouped[cat] = [];
          grouped[cat].push(item);
        }
      }
    } catch (e) {
      console.error("Fehler beim Laden der Liste", e);
    }
  }

  async function generateGrocery() {
    const token = localStorage.getItem(TOKEN_KEY);

    try {
      const res = await fetch(`${API_BASE}/grocery/generate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        loadGrocery();
      }
    } catch (e) {
      console.error("Fehler bei Generierung", e);
    }
  }

  if (typeof window !== "undefined") {
    loadGrocery();
  }

  const categoryLabels: Record<string, string> = {
    vegetables: "🥦 Gemüse",
    fruit: "🍎 Obst",
    meat: "🥩 Fleisch",
    dairy: "🥛 Milchprodukte",
    grains: "🌾 Getreide",
    spices: "🧂 Gewürze",
    canned: "🥫 Konserven",
    frozen: "❄️ Tiefkühl",
    condiments: "🍯 Soßen & Co.",
    other: "📦 Sonstiges",
  };

  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">🛒 Einkaufsliste</h1>
        <button
          onClick={generateGrocery}
          className="rounded-lg bg-sprossa-green px-4 py-2 text-sm text-white"
        >
          + Neue Liste generieren
        </button>
      </div>

      {selectedList && (
        <p className="mb-6 text-gray-600 text-sm">
          {selectedList.week_number ? `Woche ${selectedList.week_number}` : "Monatsliste"}
          {" · "}generiert am {new Date(selectedList.generated_at).toLocaleDateString("de")}
        </p>
      )}

      {/* Listen-Auswahl */}
      {groceryLists.length > 1 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {groceryLists.map((l) => (
            <button
              key={l.id}
              onClick={() => selectList(l.id)}
              className={`rounded-lg px-3 py-1 text-sm ${
                selectedList?.id === l.id
                  ? "bg-sprossa-green text-white"
                  : "border border-gray-300 text-gray-700"
              }`}
            >
              {l.week_number ? `Woche ${l.week_number}` : "Monat"}
            </button>
          ))}
        </div>
      )}

      {/* Nach Kategorien gruppiert */}
      {Object.keys(grouped).length > 0
        ? Object.entries(grouped).map(([cat, items]) => (
            <div key={cat} className="mb-4 rounded-lg border border-gray-200 p-4">
              <h2 className="mb-2 font-semibold text-lg">
                {categoryLabels[cat] || cat}
              </h2>
              <ul className="space-y-1">
                {items.map((item: any) => (
                  <li key={item.id} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className={`text-sm ${item.is_checked ? "line-through text-gray-400" : ""}`}>
                      {item.ingredient_name || "Zutat"}
                      {" ("}{item.quantity_total} {item.unit}{")"}
                    </span>
                    {item.notes && (
                      <span className="text-xs text-gray-400">— {item.notes}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))
        : (
          <div className="rounded-lg border border-gray-200 p-8 text-center">
            <p className="mb-4 text-gray-600">Noch keine Einkaufsliste vorhanden.</p>
            <button
              onClick={generateGrocery}
              className="rounded-lg bg-sprossa-green px-6 py-2 text-white"
            >
              🛒 Erste Liste generieren
            </button>
          </div>
        )}
    </section>
  );
}