"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { authHeaders, getApiBase } from "../../lib/auth";

const difficultyLabels: Record<string, string> = {
  easy: "Einfach",
  medium: "Mittel",
  hard: "Fortgeschritten",
};

function normalizeList(payload: any): any[] {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.recipes)) return payload.recipes;
  return [];
}

export default function RecipesPage() {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [tagOptions, setTagOptions] = useState<string[]>([]);
  const [plannedIds, setPlannedIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [maxTime, setMaxTime] = useState("");
  const [tag, setTag] = useState("");
  const [filterPlanned, setFilterPlanned] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [visibleCount, setVisibleCount] = useState(12);

  // Suche entprellen, damit nicht bei jedem Tastendruck neu geladen wird
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  // Einmalig: verfügbare Tags + geplante Rezept-IDs
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${getApiBase()}/recipes`, { headers: authHeaders() });
        const all = r.ok ? normalizeList(await r.json()) : [];
        const tags = new Set<string>();
        for (const rec of all) for (const t of rec.tags || []) if (t) tags.add(t);
        setTagOptions([...tags].sort((a, b) => a.localeCompare(b, "de")));
      } catch (e) {
        setError("Fehler beim Laden der Rezepte");
      }

      try {
        const p = await fetch(`${getApiBase()}/plans`, { headers: authHeaders() });
        if (p.ok) {
          const plans = normalizeList(await p.json());
          const ids = new Set<string>();
          for (const plan of plans) {
            try {
              const w = await fetch(`${getApiBase()}/plans/${plan.id}/weeks`, { headers: authHeaders() });
              if (w.ok) {
                for (const week of normalizeList(await w.json())) {
                  for (const slot of week.meal_slots || []) {
                    if (slot.recipe_id) ids.add(slot.recipe_id);
                  }
                }
              }
            } catch (e) {
              setError("Fehler beim Laden der Rezepte");
            }
          }
          setPlannedIds(ids);
        }
      } catch (e) {
        setError("Fehler beim Laden der Rezepte");
      }
    })();
  }, []);

  const loadRecipes = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (debouncedSearch) params.set("search", debouncedSearch);
      if (difficulty) params.set("difficulty", difficulty);
      if (maxTime) params.set("max_time", maxTime);
      if (tag) params.set("tag", tag);
      if (filterPlanned) params.set("planned_only", "true");
      const qs = params.toString();
      const r = await fetch(`${getApiBase()}/recipes${qs ? `?${qs}` : ""}`, { headers: authHeaders() });
      setRecipes(r.ok ? normalizeList(await r.json()) : []);
    } catch (e) {
      setError("Fehler beim Laden der Rezepte");
    }
    setLoading(false);
  }, [debouncedSearch, difficulty, maxTime, tag, filterPlanned]);

  useEffect(() => {
    setVisibleCount(12);
    loadRecipes();
  }, [loadRecipes]);

  const hasFilters = Boolean(search || difficulty || maxTime || tag || filterPlanned);

  function resetFilters() {
    setSearch("");
    setDifficulty("");
    setMaxTime("");
    setTag("");
    setFilterPlanned(false);
  }

  if (loading && recipes.length === 0) return (
    <section className="py-8">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 p-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-sprossa-muted/10 rounded-xl h-24" />
        ))}
      </div>
    </section>
  );

  return (
    <section className="py-8">
      <div className="mb-4"><Link href="/dashboard" className="text-sprossa-green text-sm hover:underline">← Dashboard</Link></div>
      <h1 className="mb-4 font-display text-3xl font-bold text-sprossa-ink">📖 Rezepte ({recipes.length})</h1>

      {/* Suche + Filter */}
      <div className="mb-6 space-y-3">
        <input type="search" placeholder="🔍 Rezept suchen…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink" />

        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs font-semibold text-sprossa-muted">
            Schwierigkeit
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}
              className="rounded-xl border border-sprossa-muted/20 bg-white px-3 py-2 text-sm font-normal text-sprossa-ink">
              <option value="">Alle</option>
              <option value="easy">Einfach</option>
              <option value="medium">Mittel</option>
              <option value="hard">Fortgeschritten</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-semibold text-sprossa-muted">
            Max. Zeit
            <select value={maxTime} onChange={(e) => setMaxTime(e.target.value)}
              className="rounded-xl border border-sprossa-muted/20 bg-white px-3 py-2 text-sm font-normal text-sprossa-ink">
              <option value="">Alle</option>
              <option value="15">≤ 15 Min</option>
              <option value="30">≤ 30 Min</option>
              <option value="45">≤ 45 Min</option>
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-semibold text-sprossa-muted">
            Tag / Diet
            <select value={tag} onChange={(e) => setTag(e.target.value)}
              className="rounded-xl border border-sprossa-muted/20 bg-white px-3 py-2 text-sm font-normal text-sprossa-ink">
              <option value="">Alle</option>
              {tagOptions.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>

          <label className="touch-target flex cursor-pointer items-center gap-2 py-2 text-sm text-sprossa-muted">
            <input type="checkbox" checked={filterPlanned} onChange={(e) => setFilterPlanned(e.target.checked)}
              className="h-4 w-4 rounded border-sprossa-muted/30 text-sprossa-green" />
            Nur geplante Rezepte
          </label>

          {hasFilters && (
            <button onClick={resetFilters} className="rounded-lg border border-sprossa-muted/30 px-3 py-2 text-sm font-bold text-sprossa-ink hover:bg-sprossa-sage">
              Filter zurücksetzen
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Recipe Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {recipes.length > 0 ? recipes.slice(0, visibleCount).map((r) => (
          <Link key={r.id} href={`/dashboard/recipes/${r.id}`}
            className="group block rounded-xl border border-sprossa-ink/10 bg-white p-4 transition-all hover:shadow-md hover:border-sprossa-green/40 hover:-translate-y-0.5">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-semibold text-lg text-sprossa-ink group-hover:text-sprossa-green">{r.title}</h3>
              {r.cook_once_eat_twice && <span className="rounded bg-sprossa-sage px-2 py-0.5 text-xs text-sprossa-dark">⟲ Cook Once</span>}
            </div>
            <div className="mb-2 flex gap-2 text-xs text-sprossa-muted flex-wrap">
              <span>🍽 {r.servings} Port.</span>
              <span>⏱ {(r.prep_time_minutes||0)+(r.cook_time_minutes||0)} Min</span>
              <span>📊 {difficultyLabels[r.difficulty] || "Fortgeschritten"}</span>
              {plannedIds.has(r.id) && <span className="text-sprossa-green">✅ im Plan</span>}
            </div>
            <p className="mb-2 text-sm text-sprossa-muted line-clamp-2">{r.description || ""}</p>
            <div className="flex flex-wrap gap-1">{(r.tags || []).map((t: string) => (
              <span key={t} className="rounded bg-sprossa-sage px-2 py-0.5 text-xs text-sprossa-dark">{t}</span>
            ))}</div>
          </Link>
        )) : (
          <div className="col-span-full rounded-xl border border-sprossa-ink/10 bg-white p-8 text-center">
            <p className="text-sprossa-muted">
              {hasFilters ? "Keine Rezepte für die gewählten Filter gefunden." : "Keine Rezepte gefunden."}
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {recipes.length > visibleCount && (
        <div className="mt-6 text-center">
          <p className="mb-2 text-sm text-sprossa-muted">
            Zeige {Math.min(visibleCount, recipes.length)} von {recipes.length} Rezepten
          </p>
          <button onClick={() => setVisibleCount(visibleCount + 12)}
            className="rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark">
            Weitere laden …
          </button>
        </div>
      )}
    </section>
  );
}
