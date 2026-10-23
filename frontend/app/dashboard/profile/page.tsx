"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authHeaders, getApiBase } from "../../lib/auth";

type DietType = "fleisch" | "fisch" | "vegetarisch" | "vegan";
type Allergy = "gluten" | "laktose" | "nüsse" | "ei" | "soja";
type Cuisine = "deutsch" | "italienisch" | "asiatisch" | "orientalisch" | "mexikanisch";
type Supermarket = "aldi" | "rewe" | "edeka" | "lidl" | "anderer";
type ShoppingFrequency = "1x_woche" | "2x_woche" | "mehrmals_woche" | "nach_bedarf";
type BudgetRange = "under_200" | "200_400" | "400_600" | "600_800" | "over_800";
type TimeBudget = "under_15" | "15_30" | "30_45" | "over_45";

const DIET_LABELS: Record<string, string> = {
  fleisch: "🥩 Fleisch",
  fisch: "🐟 Fisch",
  vegetarisch: "🥦 Vegetarisch",
  vegan: "🌱 Vegan",
};
const ALLERGY_LABELS: Record<string, string> = {
  gluten: "🌾 Gluten",
  laktose: "🥛 Laktose",
  nüsse: "🥜 Nüsse",
  ei: "🥚 Ei",
  soja: "🫘 Soja",
};
const CUISINE_LABELS: Record<string, string> = {
  deutsch: "🇩🇪 Deutsch",
  italienisch: "🍝 Italienisch",
  asiatisch: "🥟 Asiatisch",
  orientalisch: "🧆 Orientalisch",
  mexikanisch: "🌮 Mexikanisch",
};
const SUPERMARKET_LABELS: Record<string, string> = {
  aldi: "Aldi", rewe: "Rewe", edeka: "Edeka", lidl: "Lidl", anderer: "Anderer",
};
const BUDGET_LABELS: Record<string, string> = {
  under_200: "< 200 €", "200_400": "200–400 €", "400_600": "400–600 €",
  "600_800": "600–800 €", over_800: "800+ €",
};
const FREQUENCY_LABELS: Record<string, string> = {
  "1x_woche": "1×/Woche", "2x_woche": "2×/Woche",
  mehrmals_woche: "Mehrmals/Woche", nach_bedarf: "Nach Bedarf",
};

export default function ProfilePage() {
  const router = useRouter();
  const [householdId, setHouseholdId] = useState<string | null>(null);
  const [householdName, setHouseholdName] = useState("Mein Haushalt");
  const [members, setMembers] = useState<any[]>([]);
  const [newName, setNewName] = useState("");
  const [newAge, setNewAge] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const [error, setError] = useState("");

  // Dietary profile fields
  let dietaryProfile: any = {};
  const [dietTypes, setDietTypes] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [dislikedIngredients, setDislikedIngredients] = useState("");
  const [supermarket, setSupermarket] = useState<string | null>(null);
  const [budgetRange, setBudgetRange] = useState<string | null>(null);
  const [shoppingFrequency, setShoppingFrequency] = useState<string | null>(null);
  const [timeBudget, setTimeBudget] = useState<string | null>(null);

  // Member portion factors
  const [portionFactors, setPortionFactors] = useState<Record<string, number>>({});

  useEffect(() => {
    loadHousehold();
  }, []);

  function ageBasedPortionFactor(age: number | null): number {
    if (!age) return 1.0;
    if (age < 3) return 0.5;
    if (age < 6) return 0.7;
    if (age < 10) return 0.85;
    if (age < 14) return 1.0;
    if (age >= 65) return 0.8;
    return 1.0;
  }

  async function loadHousehold() {
    try {
      const hhRes = await fetch(`${getApiBase()}/households`, { headers: authHeaders() });
      if (!hhRes.ok) { setLoading(false); return; }
      const hhList = await hhRes.json();
      if (hhList.length > 0) {
        const hh = hhList[0];
        setHouseholdId(hh.id);
        setHouseholdName(hh.name);
        const dp = hh.dietary_profile || {};
        dietaryProfile = dp;
        setDietTypes(dp.diet_types || []);
        setAllergies(dp.allergies || []);
        setCuisines(dp.preferred_cuisines || []);
        setDislikedIngredients(dp.disliked_ingredients || "");
        setSupermarket(dp.preferred_supermarket || null);
        setBudgetRange(dp.monthly_budget_range || null);
        setShoppingFrequency(dp.shopping_frequency || null);
        setTimeBudget(dp.time_budget || null);

        const mRes = await fetch(`${getApiBase()}/households/${hh.id}/members`, { headers: authHeaders() });
        if (mRes.ok) {
          const mList = await mRes.json();
          setMembers(mList);
          // Initialize portion factors
          const pf: Record<string, number> = {};
          for (const m of mList) {
            pf[m.id] = ageBasedPortionFactor(m.age);
          }
          setPortionFactors(pf);
        }
      }
    } catch (e: any) {
      setError(e.message || "Fehler beim Laden des Profils");
    }
    setLoading(false);
  }

  async function saveHousehold() {
    if (!householdId) return;
    setSaving(true);
    setSaveMsg("");
    setError("");
    try {
      const dp: any = {
        diet_types: dietTypes,
        allergies: allergies,
        preferred_cuisines: cuisines,
        disliked_ingredients: dislikedIngredients,
        preferred_supermarket: supermarket,
        monthly_budget_range: budgetRange,
        shopping_frequency: shoppingFrequency,
        time_budget: timeBudget,
      };
      const res = await fetch(`${getApiBase()}/households/${householdId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ name: householdName, dietary_profile: dp }),
      });
      if (res.ok) {
        setSaveMsg("✅ Gespeichert!");
        setTimeout(() => setSaveMsg(""), 3000);
      } else {
        setSaveMsg("❌ Fehler beim Speichern");
      }
    } catch (e: any) {
      setError(e.message || "Fehler beim Speichern des Profils");
    }
    setSaving(false);
  }

  async function addMember() {
    if (!householdId || !newName) return;
    setError("");
    try {
      await fetch(`${getApiBase()}/households/${householdId}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ name: newName, age: newAge }),
      });
      setNewName(""); setNewAge(null);
      await loadHousehold();
    } catch (e: any) {
      setError(e.message || "Fehler beim Hinzufügen des Mitglieds");
    }
  }

  async function removeMember(mid: string) {
    if (!householdId) return;
    setError("");
    try {
      await fetch(`${getApiBase()}/households/${householdId}/members/${mid}`, {
        method: "DELETE", headers: authHeaders(),
      });
      await loadHousehold();
    } catch (e: any) {
      setError(e.message || "Fehler beim Entfernen des Mitglieds");
    }
  }

  // ─── Toggle helpers ──────────────────────────────────────────────────────

  function toggleArray(arr: string[], val: string, setter: (v: string[]) => void) {
    if (arr.includes(val)) setter(arr.filter((x) => x !== val));
    else setter([...arr, val]);
  }

  if (loading) return <div className="p-8 text-center text-sprossa-muted">Lade Profil…</div>;

  return (
    <section className="py-8">
      <div className="mb-4"><Link href="/dashboard" className="text-sprossa-green text-sm">← Zurück zum Dashboard</Link></div>
      <h1 className="mb-6 font-display text-3xl font-bold text-sprossa-ink">👤 Profil – {householdName}</h1>

      {/* ═══ Sektion 1: Haushalt & Mitglieder ═══ */}
      <div className="mb-8 rounded-xl border border-sprossa-ink/10 bg-white p-6">
        <h2 className="mb-4 font-display text-xl font-semibold text-sprossa-ink">🏠 Haushalt & Mitglieder</h2>
        <div className="space-y-3">
          <input type="text" className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
            value={householdName} onChange={(e) => setHouseholdName(e.target.value)} />
        </div>

        <ul className="mt-4 mb-4 space-y-2">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between border-b border-sprossa-ink/10 pb-2">
              <span className="text-sprossa-ink">{m.name}{m.age ? ` (${m.age} J.)` : ""}</span>
              <button onClick={() => removeMember(m.id)} className="rounded bg-sprossa-error px-3 py-1 text-xs text-white">Entfernen</button>
            </li>
          ))}
        </ul>
        <div className="flex gap-3">
          <input type="text" placeholder="Name" className="rounded-xl border border-sprossa-muted/20 px-4 py-2 text-sprossa-ink"
            value={newName} onChange={(e) => setNewName(e.target.value)} />
          <input type="number" placeholder="Alter" className="w-20 rounded-xl border border-sprossa-muted/20 px-4 py-2 text-sprossa-ink"
            value={newAge || ""} onChange={(e) => setNewAge(parseInt(e.target.value) || null)} />
          <button onClick={addMember} className="rounded-xl bg-sprossa-green px-4 py-2 font-bold text-white hover:bg-sprossa-dark">Hinzufügen</button>
        </div>
      </div>

      {/* ═══ Sektion 2: Ernährungsprofil ═══ */}
      <div className="mb-8 rounded-xl border border-sprossa-ink/10 bg-white p-6">
        <h2 className="mb-4 font-display text-xl font-semibold text-sprossa-ink">🥗 Ernährungsprofil</h2>

        {/* Ess-Typ */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Esst ihr…</h3>
          <div className="flex flex-wrap gap-2">
            {(["fleisch", "fisch", "vegetarisch", "vegan"] as string[]).map((t) => (
              <button key={t} onClick={() => toggleArray(dietTypes, t, setDietTypes)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${dietTypes.includes(t) ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{DIET_LABELS[t]}</button>
            ))}
          </div>
        </div>

        {/* Allergien */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Allergien & Unverträglichkeiten</h3>
          <div className="flex flex-wrap gap-2">
            {(["gluten", "laktose", "nüsse", "ei", "soja"] as string[]).map((a) => (
              <button key={a} onClick={() => toggleArray(allergies, a, setAllergies)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${allergies.includes(a) ? "border-sprossa-terracotta bg-sprossa-terracotta/10 text-sprossa-terracotta" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{ALLERGY_LABELS[a]}</button>
            ))}
          </div>
        </div>

        {/* Küchen-Präferenzen */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Küchen-Präferenzen</h3>
          <div className="flex flex-wrap gap-2">
            {(["deutsch", "italienisch", "asiatisch", "orientalisch", "mexikanisch"] as string[]).map((c) => (
              <button key={c} onClick={() => toggleArray(cuisines, c, setCuisines)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${cuisines.includes(c) ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{CUISINE_LABELS[c]}</button>
            ))}
          </div>
        </div>

        {/* Abneigungen */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Abneigungen</h3>
          <p className="mb-1 text-xs text-sprossa-muted">Kommasepariert, z.B. „Pilze, Innereien, Rote Bete"</p>
          <input type="text" className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-2 text-sprossa-ink"
            value={dislikedIngredients} onChange={(e) => setDislikedIngredients(e.target.value)}
            placeholder="Pilze, Innereien, Rote Bete" />
        </div>
      </div>

      {/* ═══ Sektion 3: Einkaufsdaten & Portionen ═══ */}
      <div className="mb-8 rounded-xl border border-sprossa-ink/10 bg-white p-6">
        <h2 className="mb-4 font-display text-xl font-semibold text-sprossa-ink">🛒 Einkaufsdaten & Portionen</h2>

        {/* Supermarkt */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Wo kauft ihr ein?</h3>
          <div className="flex flex-wrap gap-2">
            {(["aldi", "rewe", "edeka", "lidl", "anderer"] as string[]).map((s) => (
              <button key={s} onClick={() => setSupermarket(s)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${supermarket === s ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{SUPERMARKET_LABELS[s]}</button>
            ))}
          </div>
        </div>

        {/* Budget */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Monatliches Budget</h3>
          <div className="flex flex-wrap gap-2">
            {(["under_200", "200_400", "400_600", "600_800", "over_800"] as string[]).map((b) => (
              <button key={b} onClick={() => setBudgetRange(b)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${budgetRange === b ? "border-sprossa-terracotta bg-sprossa-terracotta/10 text-sprossa-terracotta" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{BUDGET_LABELS[b]}</button>
            ))}
          </div>
        </div>

        {/* Shopping frequency */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Wie oft kauft ihr ein?</h3>
          <div className="flex flex-wrap gap-2">
            {(["1x_woche", "2x_woche", "mehrmals_woche", "nach_bedarf"] as string[]).map((f) => (
              <button key={f} onClick={() => setShoppingFrequency(f)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${shoppingFrequency === f ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{FREQUENCY_LABELS[f]}</button>
            ))}
          </div>
        </div>

        {/* Portions-Faktoren */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Portions-Faktoren</h3>
          <p className="mb-1 text-xs text-sprossa-muted">Altersbasierter Vorschlag (manuell überschreibbar).</p>
          <div className="space-y-2">
            {members.map((m) => (
              <div key={m.id} className="flex items-center gap-3">
                <span className="text-sm text-sprossa-ink w-32">{m.name}{m.age ? ` (${m.age} J.)` : ""}</span>
                <input type="range" min="0.25" max="2.0" step="0.05"
                  value={portionFactors[m.id] || 1.0}
                  onChange={(e) => {
                    const pf = {...portionFactors};
                    pf[m.id] = parseFloat(e.target.value);
                    setPortionFactors(pf);
                  }}
                  className="flex-1 accent-sprossa-green" />
                <span className="text-sm font-bold text-sprossa-ink">×{portionFactors[m.id]?.toFixed(2) || "1.00"}</span>
              </div>
            ))}
          </div>
          {members.length > 0 && (
            <p className="mt-2 text-xs text-sprossa-muted">
              Gesamtfaktor: {members.reduce((sum, m) => sum + (portionFactors[m.id] || 1.0), 0.0).toFixed(2)}
            </p>
          )}
        </div>

        {/* Zeitbudget */}
        <div className="mb-4">
          <h3 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Zeitbudget</h3>
          <div className="flex flex-wrap gap-2">
            {["under_15", "15_30", "30_45", "over_45"].map((t) => (
              <button key={t} onClick={() => setTimeBudget(t)}
                className={(`rounded-xl border-2 px-3 py-2 text-sm font-bold transition-all ${timeBudget === t ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green" : "border-sprossa-muted/20 bg-white text-sprossa-muted"}`)}>{t === "under_15" ? "< 15 Min" : t === "15_30" ? "15–30 Min" : t === "30_45" ? "30–45 Min" : "> 45 Min"}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Save button */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={saveHousehold} disabled={saving}
          className="rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark disabled:opacity-60">
          {saving ? "Wird gespeichert…" : "💾 Speichern"}
        </button>
        {saveMsg && <span className="text-sm font-medium text-sprossa-ink">{saveMsg}</span>}
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-sprossa-ink/10 bg-white p-6">
        <h2 className="mb-2 font-display text-xl font-semibold text-sprossa-ink">🔐 Authentifizierung</h2>
        <p className="text-sm text-sprossa-muted">Session läuft über httpOnly-Cookie</p>
      </div>
    </section>
  );
}
