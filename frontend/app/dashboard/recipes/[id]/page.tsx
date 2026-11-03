"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { authHeaders, getApiBase } from "../../../lib/auth";
import { formatQuantity } from "../../../lib/format";

const TRIVIAL_TIPS = [
  "mit kindern zusammen kochen.",
  "kinder können helfen.",
  "gemeinsam genießen.",
  "gemeinsam kochen.",
  "kinder können mithelfen.",
];

/**
 * Zerlegt `instructions` robust in einzelne Schritte:
 * - nummeriert ("1. … 2. …", auch ohne Zeilenumbrüche)
 * - durch Leerzeilen getrennt
 * - durch einfache Zeilenumbrüche getrennt
 * - sonst ein einzelner Schritt
 */
function parseInstructions(raw: string | null | undefined): string[] {
  const text = (raw || "").trim();
  if (!text) return [];

  // Nummerierte Variante: mindestens zwei "1." / "2)" / "3." Marker
  const numbered = text
    .split(/(?:^|\s)\d{1,2}[.)]\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  if (numbered.length >= 2) return numbered;

  if (/\n\s*\n/.test(text)) {
    return text.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);
  }

  const lines = text.split(/\n+/).map((s) => s.trim()).filter(Boolean);
  if (lines.length > 1) return lines;

  // Einzelner nummerierter Schritt: Nummer entfernen, damit sie nicht doppelt erscheint
  const single = text.replace(/^\s*\d{1,2}[.)]\s+/, "").trim();
  return [single || text];
}

/** Zahl mit deutschem Komma, ohne unnötige Nachkommastellen (3.7 -> "3,7", 185.0 -> "185"). */
function formatNumber(value: unknown): string {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value ?? "");
  return n.toFixed(2).replace(/\.?0+$/, "").replace(".", ",");
}

const catLabels: Record<string, string> = {
  vegetables: "🥦 Gemüse", fruit: "🍎 Obst", meat: "🥩 Fleisch/Fisch", dairy: "🥛 Milchprodukte",
  grains: "🌾 Getreide", spices: "🧂 Gewürze", canned: "🥫 Konserven", frozen: "❄️ Tiefkühl",
  condiments: "🍯 Öle & Soßen", other: "📦 Sonstiges",
};

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [recipe, setRecipe] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [checked, setChecked] = useState<Set<string>>(new Set());

  // Bug 76: Portions-Multiplier aus dem Plan-Link (?multiplier=0.925).
  // Direktaufruf aus der Rezeptliste hat keinen Parameter -> 1.0 (Basiswerte).
  const rawMultiplier = Number(searchParams.get("multiplier") ?? 1);
  const multiplier = Number.isFinite(rawMultiplier) && rawMultiplier >= 0.1 && rawMultiplier <= 20
    ? rawMultiplier
    : 1;
  const isScaled = Math.abs(multiplier - 1) > 1e-6;

  useEffect(() => {
    fetch(`${getApiBase()}/recipes/${params.id}?multiplier=${multiplier}`, { headers: authHeaders() })
      .then(r => r.ok ? r.json() : null)
      .then(d => { setRecipe(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [params.id, multiplier]);

  if (loading) return <p className="p-8 text-center text-sprossa-muted">Lade Rezept…</p>;
  if (!recipe) return <p className="p-8 text-center text-sprossa-muted">Rezept nicht gefunden.</p>;

  const instructions = parseInstructions(recipe.instructions);
  const totalMin = (recipe.prep_time_minutes || 0) + (recipe.cook_time_minutes || 0);
  const kidTip = (recipe.kid_friendly_tip || "").trim();
  const normalizeTip = (s: string) => s.toLowerCase().replace(/[.!?]+$/, "").replace(/\s+/g, " ").trim();
  const showKidTip = kidTip.length > 15 && !TRIVIAL_TIPS.map(normalizeTip).includes(normalizeTip(kidTip));

  return (
    <section className="mx-auto max-w-[820px] py-8">
      <div className="mb-4"><Link href="/dashboard/recipes" className="text-sprossa-green text-sm hover:underline">← Alle Rezepte</Link></div>

      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3 mb-2">
          <h1 className="font-display text-3xl font-bold text-sprossa-ink">{recipe.title}</h1>
          {recipe.cook_once_eat_twice && (
            <span className="rounded-full bg-sprossa-sage px-3 py-1 text-xs font-bold text-sprossa-dark">⟲ Cook Once, Eat Twice</span>
          )}
        </div>
        <p className="text-sprossa-muted mb-4">{recipe.description}</p>

        {/* Bug 76: Hinweis, wenn aus dem Plan mit angepasster Portionszahl geöffnet */}
        {isScaled && (
          <div className="mb-4 rounded-xl border border-sprossa-green/30 bg-sprossa-sage/40 px-4 py-3 text-sm font-medium text-sprossa-dark">
            📐 Mengen angepasst für {formatNumber(recipe.servings)} Portionen (Plan-Portionen)
          </div>
        )}

        {/* Meta-Infos */}
        <div className="flex flex-wrap gap-4 text-sm">
          <span className="rounded-xl bg-sprossa-sage px-4 py-2 font-semibold text-sprossa-ink">🍽 {formatNumber(recipe.servings)} Portionen</span>
          <span className="rounded-xl bg-sprossa-sage px-4 py-2 font-semibold text-sprossa-ink">⏱ {totalMin} Min.</span>
          <span className="rounded-xl bg-sprossa-sage px-4 py-2 font-semibold text-sprossa-ink">📊 {recipe.difficulty === "easy" ? "Einfach" : recipe.difficulty === "medium" ? "Mittel" : "Fortgeschritten"}</span>
          {recipe.prep_time_minutes > 0 && <span className="rounded-xl bg-sprossa-sage px-4 py-2 font-semibold text-sprossa-ink">🔪 {recipe.prep_time_minutes} Min. Vorbereitung</span>}
          {recipe.cook_time_minutes > 0 && <span className="rounded-xl bg-sprossa-sage px-4 py-2 font-semibold text-sprossa-ink">🍳 {recipe.cook_time_minutes} Min. Kochzeit</span>}
        </div>

        {/* Tags */}
        {(recipe.tags || []).length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {(recipe.tags as string[]).map((t: string) => (
              <span key={t} className="rounded-full bg-sprossa-cream px-3 py-1 text-xs font-medium text-sprossa-muted">{t}</span>
            ))}
          </div>
        )}
      </div>

      <div className="grid gap-8 md:grid-cols-[320px_1fr]">
        {/* Zutaten (links) */}
        <div>
          <div className="rounded-xl border border-sprossa-ink/10 bg-white p-5">
            <h2 className="mb-4 font-display text-xl font-semibold text-sprossa-green">📋 Zutaten</h2>

            {/* Nach Kategorie gruppiert */}
            {Object.entries(
              (recipe.ingredients || []).reduce((acc: any, ing: any) => {
                const cat = ing.category || "other";
                if (!acc[cat]) acc[cat] = [];
                acc[cat].push(ing);
                return acc;
              }, {})
            ).map(([cat, items]: [string, any]) => (
              <div key={cat} className="mb-4">
                <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-sprossa-muted">{catLabels[cat] || cat}</h3>
                <ul className="space-y-2">
                  {items.map((ing: any, i: number) => {
                    const key = `${cat}-${i}`;
                    const label = ing.name || ing.ingredient_name || "Zutat";
                    return (
                      <li key={key} className="touch-target flex items-center gap-3">
                        <input type="checkbox" checked={checked.has(key)} onChange={() => {
                          const s = new Set(checked);
                          s.has(key) ? s.delete(key) : s.add(key);
                          setChecked(s);
                        }} className="h-4 w-4 rounded border-sprossa-muted/30 text-sprossa-green focus:ring-sprossa-green cursor-pointer hover:border-sprossa-green" />
                        <span className={`text-sm ${checked.has(key) ? "line-through text-sprossa-muted/50" : "text-sprossa-ink"}`}>
                          {formatQuantity(ing.quantity, ing.unit)} <strong>{label}</strong>
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>

          {/* Kinder-Tipp: nur bei echtem, nicht-trivialem Inhalt */}
          {showKidTip && (
            <div className="mt-4 rounded-xl border border-sprossa-amber/30 bg-amber-50 p-4">
              <h3 className="mb-1 font-bold text-sm text-sprossa-amber">👶 Kinder-Tipp</h3>
              <p className="text-sm text-sprossa-muted">{kidTip}</p>
            </div>
          )}
        </div>

        {/* Anleitung (rechts) */}
        <div>
          <div className="rounded-xl border border-sprossa-ink/10 bg-white p-6">
            <h2 className="mb-4 font-display text-xl font-semibold text-sprossa-green">👨‍🍳 Zubereitung</h2>
            {instructions.length > 0 ? (
              <ol className="space-y-4">
                {instructions.map((step: string, i: number) => (
                  <li key={i} className="flex gap-4">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sprossa-green text-sm font-bold text-white">{i + 1}</span>
                    <p className="pt-0.5 text-sm leading-relaxed text-sprossa-ink">{step}</p>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-sprossa-muted">Zubereitung folgt.</p>
            )}
          </div>
        </div>
      </div>

      {/* Bottom-Navigation */}
      <div className="mt-8 flex justify-between border-t border-sprossa-ink/10 pt-6">
        <Link href="/dashboard/recipes" className="text-sm font-semibold text-sprossa-green hover:underline">← Alle Rezepte</Link>
        <Link href="/dashboard/plan" className="rounded-xl bg-sprossa-green px-5 py-2 text-sm font-bold text-white hover:bg-sprossa-dark transition-colors">📅 Zum Wochenplan</Link>
      </div>
    </section>
  );
}
