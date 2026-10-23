"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authHeaders, getApiBase } from "../../lib/auth";

const categoryLabels: Record<string, string> = {
  vegetables: "🥦 Gemüse", fruit: "🍎 Obst", meat: "🥩 Fleisch", dairy: "🥛 Milchprodukte",
  grains: "🌾 Getreide", spices: "🧂 Gewürze", canned: "🥫 Konserven", frozen: "❄️ Tiefkühl",
  condiments: "🍯 Soßen & Co.", other: "📦 Sonstiges",
};

function currentWeek(): number {
  const d = new Date(); const s = d.getTime();
  const y = d.getFullYear();
  const jan1 = new Date(y, 0, 1);
  const days = Math.floor((s - jan1.getTime()) / 86400000);
  return Math.ceil((days + jan1.getDay() + 1) / 7);
}

export default function GroceryPage() {
  const router = useRouter();
  const [lists, setLists] = useState<any[]>([]);
  const [selectedList, setSelectedList] = useState<any>(null);
  const [grouped, setGrouped] = useState<Record<string, any[]>>({});
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const cw = currentWeek();

  useEffect(() => {
    loadGrocery();
  }, []);

  async function loadGrocery() {
    try {
      const r = await fetch(`${getApiBase()}/grocery-lists`, { headers: authHeaders() });
      if (!r.ok) { setLoading(false); return; }
      const data = await r.json();
      setLists(data);
      if (data.length > 0) {
        await selectList(data[0].id);
      } else {
        // Automatisch generieren wenn leer
        await fetch(`${getApiBase()}/grocery/generate`, { method: "POST", headers: authHeaders() });
        const r2 = await fetch(`${getApiBase()}/grocery-lists`, { headers: authHeaders() });
        if (r2.ok) {
          const d2 = await r2.json();
          setLists(d2);
          if (d2.length > 0) await selectList(d2[0].id);
        }
      }
    } catch (e: any) {
      setError(e.message || "Fehler beim Laden der Einkaufsliste");
    }
    setLoading(false);
  }

  async function selectList(id: string) {
    setError("");
    try {
      const list = lists.find((l) => l.id === id) || { id };
      setSelectedList(list);
      const r = await fetch(`${getApiBase()}/grocery-lists/${id}`, { headers: authHeaders() });
      if (!r.ok) return;
      const full = await r.json();
      const g: Record<string, any[]> = {};
      for (const item of full.items || []) {
        const cat = item.category || "other";
        if (!g[cat]) g[cat] = [];
        g[cat].push(item);
      }
      setGrouped(g);
      // Checkbox-Status aus localStorage laden
      const ck: Record<string, boolean> = {};
      for (const it of full.items || []) {
        if (localStorage.getItem("grocery_checked_"+it.id)) ck[it.id] = true;
      }
      setChecked(ck);
    } catch (e: any) {
      setError(e.message || "Fehler beim Laden der Liste");
    }
  }

  async function generateGrocery() {
    setError("");
    try {
      await fetch(`${getApiBase()}/grocery/generate`, { method: "POST", headers: authHeaders() });
      await loadGrocery();
    } catch (e: any) {
      setError(e.message || "Fehler beim Generieren der Liste");
    }
  }

  if (loading) return (
    <section className="py-8">
      <div className="space-y-4 p-8">
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
        <h1 className="font-display text-3xl font-bold text-sprossa-ink">🛒 Einkaufsliste</h1>
        <button onClick={generateGrocery} className="rounded-xl bg-sprossa-green px-4 py-2 font-bold text-white hover:bg-sprossa-dark">+ Neue Liste</button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Listen-Auswahl mit KW */}
      {lists.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {lists.map((l) => {
            const isCurrent = l.week_number === cw;
            return (
              <button key={l.id} onClick={() => selectList(l.id)}
                className={`rounded-lg px-3 py-1 text-sm font-bold ${selectedList?.id===l.id ? "bg-sprossa-green text-white" : isCurrent ? "bg-sprossa-dark text-white ring-2 ring-sprossa-amber" : "border border-sprossa-muted/30 text-sprossa-ink"}`}>
                KW {l.week_number}{isCurrent ? " ◀ aktuell" : ""}
              </button>
            );
          })}
        </div>
      )}

      {/* Items */}
      {Object.keys(grouped).length > 0 ? Object.entries(grouped).map(([cat, items]) => (
        <div key={cat} className="mb-4 rounded-xl border border-sprossa-ink/10 bg-white p-4">
          <h2 className="mb-2 font-semibold text-sprossa-ink">{categoryLabels[cat] || cat}</h2>
          <ul className="space-y-1">
            {items.map((item: any) => (
              <li key={item.id} className="touch-target flex items-center gap-3">
                <input type="checkbox" checked={checked[item.id] || false} onChange={() => { const s = {...checked}; if (s[item.id]) delete s[item.id]; else s[item.id] = true; setChecked(s); localStorage.setItem("grocery_checked_"+item.id, "1"); }} className="h-4 w-4 rounded border-sprossa-muted/30 text-sprossa-green cursor-pointer hover:border-sprossa-green" />
                <span className="text-sm text-sprossa-ink">{item.ingredient_name || "Zutat"} ({item.quantity_total} {item.unit})</span>
              </li>
            ))}
          </ul>
        </div>
      )) : (
        <div className="rounded-xl border border-sprossa-ink/10 bg-white p-8 text-center">
          <p className="mb-4 text-sprossa-muted">Keine Einkaufsliste vorhanden.</p>
          <button onClick={generateGrocery} className="rounded-xl bg-sprossa-green px-6 py-2 font-bold text-white">🛒 Erste Liste generieren</button>
        </div>
      )}
    </section>
  );
}
