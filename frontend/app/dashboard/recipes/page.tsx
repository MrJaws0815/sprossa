"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authHeaders, getApiBase, TOKEN_KEY } from "../../lib/auth";

export default function RecipesPage() {
  const router = useRouter();
  const [recipes, setRecipes] = useState<any[]>([]);
  const [plannedIds, setPlannedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [filterPlanned, setFilterPlanned] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) { router.push("/login"); return; }
    loadAll();
  }, []);

  async function loadAll() {
    try {
      // Alle Rezepte laden
      const r = await fetch(`${getApiBase()}/recipes`, { headers: authHeaders() });
      const data = r.ok ? await r.json() : [];
      setRecipes(data);

      // Alle PläNE laden + deren Rezept-IDs sammeln
      const p = await fetch(`${getApiBase()}/plans`, { headers: authHeaders() });
      if (p.ok) {
        const plans: any[] = await p.json();
        const ids = new Set<string>();
        for (const plan of plans) {
          try {
            const w = await fetch(`${getApiBase()}/plans/${plan.id}/weeks`, { headers: authHeaders() });
            if (w.ok) {
              const weeks: any[] = await w.json();
              for (const week of weeks) {
                for (const slot of (week.meal_slots || [])) {
                  if (slot.recipe_id) ids.add(slot.recipe_id);
                }
              }
            }
          } catch(e) { setError("Fehler beim Laden der Rezepte"); }
        }
        setPlannedIds(ids);
      }
    } catch(e) { setError("Fehler beim Laden der Rezepte"); }
    setLoading(false);
  }

  // Search + Filter
  const filtered = recipes.filter(r => {
    if (filterPlanned && !plannedIds.has(r.id)) return false;
    if (search) {
      const q = search.toLowerCase();
      const title = (r.title || "").toLowerCase();
      const desc = (r.description || "").toLowerCase();
      const tags = (r.tags || []).join(" ").toLowerCase();
      if (!title.includes(q) && !desc.includes(q) && !tags.includes(q)) return false;
    }
    return true;
  });

  if (loading) return <div className="p-8 text-center text-sprossa-muted">Lade Rezepte…</div>;

  return (
    <section className="py-8">
      <div className="mb-4"><Link href="/dashboard" className="text-sprossa-green text-sm hover:underline">← Dashboard</Link></div>
      <h1 className="mb-4 font-display text-3xl font-bold text-sprossa-ink">📖 Rezepte ({filtered.length})</h1>

      {/* Search + Filter */}
      <div className="mb-6 flex gap-3">
        <input type="search" placeholder="🔍 Rezept suchen…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink" />
        <label className="touch-target flex items-center gap-2 text-sm text-sprossa-muted cursor-pointer">
          <input type="checkbox" checked={filterPlanned} onChange={(e) => setFilterPlanned(e.target.checked)}
            className="h-4 w-4 rounded border-sprossa-muted/30 text-sprossa-green" />
          Nur geplante Rezepte
        </label>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Recipe Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.length > 0 ? filtered.map((r) => (
          <Link key={r.id} href={`/dashboard/recipes/${r.id}`}
            className="group block rounded-xl border border-sprossa-ink/10 bg-white p-4 transition-all hover:shadow-md hover:border-sprossa-green/40 hover:-translate-y-0.5">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-semibold text-lg text-sprossa-ink group-hover:text-sprossa-green">{r.title}</h3>
              {r.cook_once_eat_twice && <span className="rounded bg-sprossa-sage px-2 py-0.5 text-xs text-sprossa-dark">⟲ Cook Once</span>}
            </div>
            <div className="mb-2 flex gap-2 text-xs text-sprossa-muted flex-wrap">
              <span>🍽 {r.servings} Port.</span>
              <span>⏱ {(r.prep_time_minutes||0)+(r.cook_time_minutes||0)} Min</span>
              <span>📊 {r.difficulty === "easy" ? "Einfach" : r.difficulty === "medium" ? "Mittel" : "Fortgeschritten"}</span>
              {plannedIds.has(r.id) && <span className="text-sprossa-green">✅ im Plan</span>}
            </div>
            <p className="mb-2 text-sm text-sprossa-muted line-clamp-2">{r.description || ""}</p>
            <div className="flex flex-wrap gap-1">{(r.tags || []).map((t: string) => (
              <span key={t} className="rounded bg-sprossa-sage px-2 py-0.5 text-xs text-sprossa-dark">{t}</span>
            ))}</div>
          </Link>
        )) : (
          <div className="col-span-full rounded-xl border border-sprossa-ink/10 bg-white p-8 text-center">
            {search ? <p className="text-sprossa-muted">Keine Rezepte gefunden für "{search}"</p>
                   : <p className="text-sprossa-muted">Keine Rezepte gefunden.</p>}
          </div>
        )}
      </div>
    </section>
  );
}
