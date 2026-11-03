"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import SprossMark from "../../SprossMark";
import { authHeaders, getApiBase } from "../../lib/auth";
import { isoWeek } from "../../lib/dates";
import { formatQuantity } from "../../lib/format";

const frequencyLabels: Record<string, string> = {
  "1x_woche": "1×/Woche",
  "2x_woche": "2×/Woche",
  "mehrmals_woche": "Mehrmals/Woche",
  "nach_bedarf": "Nach Bedarf",
};

const categoryLabels: Record<string, string> = {
  vegetables: "🥦 Gemüse", fruit: "🍎 Obst", meat: "🥩 Fleisch/Fisch", fish: "🐟 Fisch",
  dairy: "🥛 Milchprodukte/Eier", grains: "🍞 Backwaren", frozen: "❄️ Tiefkühl",
  beverages: "🥤 Getränke", drinks: "🥤 Getränke", canned: "🥫 Vorrat/Konserven",
  condiments: "🍯 Soßen & Co.", spices: "🧂 Gewürze", other: "📦 Sonstiges",
};

// Supermarkt-Gang-Reihenfolge (muss zur Backend-Konstante passen)
const gangOrder = [
  "vegetables", "fruit", "meat", "fish", "dairy", "grains", "frozen",
  "beverages", "drinks", "canned", "condiments", "spices", "other",
];
function gangIndex(cat: string): number {
  const i = gangOrder.indexOf(cat);
  return i === -1 ? gangOrder.length : i;
}

/** ISO-KW des Listen-Objekts; `cw` hat Vorrang vor dem Altfeld `week_number`. */
function listWeek(l: any): number | null {
  const cw = l?.cw ?? l?.week_number;
  return typeof cw === "number" ? cw : null;
}

/** ISO-8601-KW von heute (nicht die einfache „Tage/7"-Rechnung). */
function currentISOWeek(): number {
  return isoWeek(new Date());
}

export default function GroceryPage() {
  const router = useRouter();
  const [lists, setLists] = useState<any[]>([]);
  const [selectedList, setSelectedList] = useState<any>(null);
  const [grouped, setGrouped] = useState<Record<string, any[]>>({});
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [frequency, setFrequency] = useState<string | null>(null);
  const cw = currentISOWeek();
  // Nur die neueste Liste der aktuellen ISO-KW als „aktuell" markieren.
  const currentListId = lists.find((l) => listWeek(l) === cw)?.id ?? null;

  useEffect(() => {
    loadGrocery();
  }, []);

  useEffect(() => {
    async function fetchFrequency() {
      try {
        const r = await fetch(`${getApiBase()}/households`, { headers: authHeaders() });
        if (!r.ok) return;
        const data = await r.json();
        if (Array.isArray(data) && data.length > 0) {
          const dp = data[0]?.dietary_profile || {};
          if (dp.shopping_frequency) setFrequency(dp.shopping_frequency);
        }
      } catch {
        /* Frequenz ist optional – kein Fehlerzustand nötig */
      }
    }
    fetchFrequency();
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
      // Detail-Antwort enthält cw/week_number – für Kopfzeile/Share übernehmen
      setSelectedList((prev: any) => ({ ...prev, ...full, id: full.id ?? id }));
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

  const [shareStatus, setShareStatus] = useState("");

  function buildShareText(): string {
    const lines: string[] = [];
    if (selectedList?.is_master_list) {
      lines.push("🛒 Einkaufsliste (Monatseinkauf)");
    } else {
      const week = listWeek(selectedList);
      lines.push(week != null ? `🛒 Einkaufsliste KW ${week}` : "🛒 Einkaufsliste");
    }
    for (const [cat, items] of Object.entries(grouped)) {
      lines.push("");
      lines.push(categoryLabels[cat] || cat);
      for (const item of items as any[]) {
        lines.push(`- ${item.ingredient_name || "Zutat"} (${formatQuantity(item.quantity_total, item.unit)})`);
      }
    }
    return lines.join("\n").trim();
  }

  async function handleShare() {
    const text = buildShareText();
    if (!text) return;
    try {
      if (typeof navigator !== "undefined" && navigator.share) {
        await navigator.share({ title: "Sprossa Einkaufsliste", text });
        setShareStatus("Geteilt!");
      } else if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(text);
        setShareStatus("In Zwischenablage kopiert!");
      } else {
        setShareStatus("Teilen wird von diesem Browser nicht unterstützt.");
      }
    } catch (e: any) {
      if (e?.name !== "AbortError") setShareStatus("Teilen fehlgeschlagen.");
    }
    setTimeout(() => setShareStatus(""), 3000);
  }

  function handlePrint() {
    window.print();
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
      <style>{`
        @media print {
          header, nav, .no-print { display: none !important; }
          body { background: #fff !important; color: #000 !important; }
          .print-area { margin: 0; padding: 0; }
          .print-area .rounded-xl { break-inside: avoid; border-color: #ccc !important; }
        }
      `}</style>
      <div className="mb-4 no-print"><Link href="/dashboard" className="text-sprossa-green text-sm">← Dashboard</Link></div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-display text-3xl font-bold text-sprossa-ink">
            <SprossMark size={26} color="#3A7D44" />
            <span>Einkaufsliste{selectedList?.is_master_list ? " – Monatseinkauf" : (listWeek(selectedList) != null ? ` – KW ${listWeek(selectedList)}` : "")}</span>
          </h1>
          {frequency && (
            <p className="text-sm text-sprossa-muted mt-1">
              Einkaufsfrequenz: {frequencyLabels[frequency] ?? frequency}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2 no-print">
          <button onClick={handlePrint} className="rounded-xl border border-sprossa-green px-4 py-2 font-bold text-sprossa-green hover:bg-sprossa-sage">🖨️ Drucken</button>
          <a href={selectedList ? `${getApiBase()}/grocery-lists/${selectedList.id}/export?format=csv` : "#"} className="rounded-xl border border-sprossa-green px-4 py-2 font-bold text-sprossa-green hover:bg-sprossa-sage">⬇️ Als CSV herunterladen</a>
          <button onClick={handleShare} className="rounded-xl border border-sprossa-green px-4 py-2 font-bold text-sprossa-green hover:bg-sprossa-sage">🔗 Teilen</button>
          <button onClick={generateGrocery} className="rounded-xl bg-sprossa-green px-4 py-2 font-bold text-white hover:bg-sprossa-dark">+ Neue Liste</button>
        </div>
      </div>

      {shareStatus && (
        <div className="mb-4 rounded-lg bg-sprossa-sage border border-sprossa-green p-3 text-sm text-sprossa-dark font-medium no-print">
          {shareStatus}
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Listen-Auswahl mit KW */}
      {lists.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2 no-print">
          {lists.map((l) => {
            const isCurrent = currentListId != null && l.id === currentListId;
            const label = l.is_master_list ? "Monatseinkauf" : `KW ${l.cw ?? l.week_number ?? "–"}`;
            return (
              <button key={l.id} onClick={() => selectList(l.id)}
                className={`rounded-lg px-3 py-1 text-sm font-bold ${selectedList?.id===l.id ? "bg-sprossa-green text-white" : isCurrent ? "bg-sprossa-dark text-white ring-2 ring-sprossa-amber" : "border border-sprossa-muted/30 text-sprossa-ink"}`}>
                {label}{isCurrent ? " ◀ aktuell" : ""}
              </button>
            );
          })}
        </div>
      )}

      {/* Items – nach Supermarkt-Gängen sortiert */}
      {Object.keys(grouped).length > 0 ? (
        <div className="print-area">
          {Object.entries(grouped)
            .sort(([a], [b]) => gangIndex(a) - gangIndex(b))
            .map(([cat, items]) => (
            <div key={cat} className="mb-4 rounded-xl border border-sprossa-ink/10 bg-white p-4">
              <h2 className="mb-2 font-semibold text-sprossa-ink">{categoryLabels[cat] || cat}</h2>
              <ul className="space-y-1">
                {items.map((item: any) => (
                  <li key={item.id} className="touch-target flex items-center gap-3">
                    <input type="checkbox" checked={checked[item.id] || false} onChange={() => { const s = {...checked}; if (s[item.id]) delete s[item.id]; else s[item.id] = true; setChecked(s); localStorage.setItem("grocery_checked_"+item.id, "1"); }} className="h-4 w-4 rounded border-sprossa-muted/30 text-sprossa-green cursor-pointer hover:border-sprossa-green" />
                    <span className="text-sm text-sprossa-ink">{item.ingredient_name || "Zutat"} ({formatQuantity(item.quantity_total, item.unit)})</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-sprossa-ink/10 bg-white p-8 text-center">
          <p className="mb-4 text-sprossa-muted">Keine Einkaufsliste vorhanden.</p>
          <button onClick={generateGrocery} className="rounded-xl bg-sprossa-green px-6 py-2 font-bold text-white">🛒 Erste Liste generieren</button>
        </div>
      )}
    </section>
  );
}
