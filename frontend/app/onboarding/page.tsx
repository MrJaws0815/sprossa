"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authHeaders, getApiBase } from "../lib/auth";


// ─── Member interface ────────────────────────────────────────────────────────

interface MemberInput {
  name: string;
  age: number | null;
}

// ─── Steps ───────────────────────────────────────────────────────────────────

const TOTAL_STEPS = 6; // 0-indexed: 0-5

type DietType = "fleisch" | "fisch" | "vegetarisch" | "vegan";
type Allergy = "gluten" | "laktose" | "nüsse" | "ei" | "soja";
type Cuisine = "deutsch" | "italienisch" | "asiatisch" | "orientalisch" | "mexikanisch";
type TimeBudget = "under_15" | "15_30" | "30_45" | "over_45";
type Supermarket = "aldi" | "rewe" | "edeka" | "lidl" | "anderer";
type ShoppingFrequency = "1x_woche" | "2x_woche" | "mehrmals_woche" | "nach_bedarf";
type BudgetRange = "under_200" | "200_400" | "400_600" | "600_800" | "over_800";

interface DietaryProfile {
  diet_types: DietType[];
  allergies: Allergy[];
  disliked_ingredients: string;
  preferred_cuisines: Cuisine[];
  time_budget: TimeBudget | null;
  preferred_supermarket: Supermarket | null;
  monthly_budget_range: BudgetRange | null;
  shopping_frequency: ShoppingFrequency | null;
}

const DIET_LABELS: Record<DietType, string> = {
  fleisch: "🥩 Fleisch",
  fisch: "🐟 Fisch",
  vegetarisch: "🥦 Vegetarisch",
  vegan: "🌱 Vegan",
};

const ALLERGY_LABELS: Record<Allergy, string> = {
  gluten: "🌾 Gluten",
  laktose: "🥛 Laktose",
  nüsse: "🥜 Nüsse",
  ei: "🥚 Ei",
  soja: "🫘 Soja",
};

const CUISINE_LABELS: Record<Cuisine, string> = {
  deutsch: "🇩🇪 Deutsch",
  italienisch: "🍝 Italienisch",
  asiatisch: "🥟 Asiatisch",
  orientalisch: "🧆 Orientalisch",
  mexikanisch: "🌮 Mexikanisch",
};

const TIME_OPTIONS: { value: TimeBudget; label: string; desc: string }[] = [
  { value: "under_15", label: "< 15 Min", desc: "Schnell – abends wenig Zeit" },
  { value: "15_30", label: "15–30 Min", desc: "Normale Abende" },
  { value: "30_45", label: "30–45 Min", desc: "Etwas aufwändiger" },
  { value: "over_45", label: "> 45 Min", desc: "Auch am Wochenende" },
];

const SUPERMARKET_OPTIONS: { value: Supermarket; label: string }[] = [
  { value: "aldi", label: "Aldi" },
  { value: "rewe", label: "Rewe" },
  { value: "edeka", label: "Edeka" },
  { value: "lidl", label: "Lidl" },
  { value: "anderer", label: "Anderer" },
];

const BUDGET_OPTIONS: { value: BudgetRange; label: string }[] = [
  { value: "under_200", label: "< 200 €" },
  { value: "200_400", label: "200–400 €" },
  { value: "400_600", label: "400–600 €" },
  { value: "600_800", label: "600–800 €" },
  { value: "over_800", label: "800+ €" },
];

const FREQUENCY_OPTIONS: { value: ShoppingFrequency; label: string }[] = [
  { value: "1x_woche", label: "1×/Woche" },
  { value: "2x_woche", label: "2×/Woche" },
  { value: "mehrmals_woche", label: "Mehrmals/Woche" },
  { value: "nach_bedarf", label: "Nach Bedarf" },
];

// ─── Page ──────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter();

  // Step
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Step 0 – Household name
  const [householdName, setHouseholdName] = useState("");
  const [householdId, setHouseholdId] = useState<string | null>(null);

  // Step 1 – Members
  const [members, setMembers] = useState<MemberInput[]>([
    { name: "", age: null },
  ]);

  // Step 2 – Diet type, allergies, cuisines, dislikes
  const [dietTypes, setDietTypes] = useState<DietType[]>([]);
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [cuisines, setCuisines] = useState<Cuisine[]>([]);
  const [dislikedIngredients, setDislikedIngredients] = useState("");

  // Step 3 – Shopping habits
  const [supermarket, setSupermarket] = useState<Supermarket | null>(null);
  const [budgetRange, setBudgetRange] = useState<BudgetRange | null>(null);
  const [shoppingFrequency, setShoppingFrequency] = useState<ShoppingFrequency | null>(null);

  // Step 4 – Time budget
  const [timeBudget, setTimeBudget] = useState<TimeBudget | null>(null);

  // Step 5 – Summary (final)
  const [planGenerated, setPlanGenerated] = useState(false);
  const [planResult, setPlanResult] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
  }, []);

  // ─── Helpers ────────────────────────────────────────────────────────────

  function stepTitle(): string {
    switch (step) {
      case 0: return "🏠 Haushalt";
      case 1: return "👨‍👩‍👧‍👦 Familienmitglieder";
      case 2: return "🥗 Ess-Typ & Allergien";
      case 3: return "🛒 Einkaufsgewohnheiten";
      case 4: return "⏰ Zeitbudget";
      case 5: return "🎉 Fertig!";
      default: return "";
    }
  }

  function progressPercent(): number {
    return ((step + 1) / TOTAL_STEPS) * 100;
  }

  async function createHousehold(): Promise<string | null> {
    const res = await fetch(`${getApiBase()}/households`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ name: householdName, dietary_profile: {} }),
    });
    if (!res.ok) {
      const msg = await res.json().catch(() => ({}));
      throw new Error((msg as any).detail || "Haushalt konnte nicht erstellt werden");
    }
    const data = await res.json();
    return data.id;
  }

  async function addMembers(hid: string): Promise<void> {
    for (const m of members) {
      if (!m.name.trim()) continue;
      const res = await fetch(`${getApiBase()}/households/${hid}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ name: m.name.trim(), age: m.age }),
      });
      if (!res.ok) {
        const msg = await res.json().catch(() => ({}));
        throw new Error((msg as any).detail || `Mitglied "${m.name}" konnte nicht hinzugefügt werden`);
      }
    }
  }

  async function saveDietaryProfile(hid: string): Promise<void> {
    const dietaryProfile: DietaryProfile = {
      diet_types: dietTypes,
      allergies: allergies,
      disliked_ingredients: dislikedIngredients,
      preferred_cuisines: cuisines,
      time_budget: timeBudget,
      preferred_supermarket: supermarket,
      monthly_budget_range: budgetRange,
      shopping_frequency: shoppingFrequency,
    };
    const res = await fetch(`${getApiBase()}/households/${hid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ dietary_profile: dietaryProfile }),
    });
    if (!res.ok) {
      throw new Error("Ernährungsprofil konnte nicht gespeichert werden");
    }
  }

  async function generatePlan(): Promise<void> {
    const now = new Date();
    const res = await fetch(`${getApiBase()}/plans/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ month: now.getMonth() + 1, year: now.getFullYear() }),
    });
    if (!res.ok) {
      // Non-fatal – user can generate later from dashboard
      setPlanResult("⚠️ Plan konnte nicht automatisch erstellt werden. Du kannst ihn später im Dashboard generieren.");
      return;
    }
    const data = await res.json();
    setPlanResult(`✅ Plan für ${data.month}/${data.year} mit ${data.weeks} Wochen erstellt.`);
  }

  // ─── Step navigation ────────────────────────────────────────────────────

  function canProceed(): boolean {
    switch (step) {
      case 0: return householdName.trim().length >= 2;
      case 1: {
        const valid = members.filter((m) => m.name.trim().length > 0);
        return valid.length >= 1 && valid.length <= 8;
      }
      case 2: return dietTypes.length > 0; // allergies, cuisines, dislikes optional
      case 3: return supermarket !== null && budgetRange !== null && shoppingFrequency !== null;
      case 4: return timeBudget !== null;
      case 5: return true;
      default: return false;
    }
  }

  function nextStepLabel(): string {
    if (step === TOTAL_STEPS - 1) return "📊 Zum Dashboard";
    return "Weiter →";
  }

  async function handleNext() {
    setError("");

    if (step === 0) {
      // Create household
      setLoading(true);
      try {
        const hid = await createHousehold();
        if (hid) {
          setHouseholdId(hid);
          setStep(1);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (step === 1 && householdId) {
      // Save members
      setLoading(true);
      try {
        await addMembers(householdId);
        setStep(2);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (step === 2 && householdId) {
      // Save diet types, allergies, cuisines, dislikes
      setLoading(true);
      try {
        await saveDietaryProfile(householdId);
        setStep(3);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (step === 3 && householdId) {
      // Save shopping habits
      setLoading(true);
      try {
        await saveDietaryProfile(householdId);
        setStep(4);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (step === 4 && householdId) {
      // Save time budget
      setLoading(true);
      try {
        await saveDietaryProfile(householdId);
        setStep(5);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
      return;
    }

    if (step === 5) {
      // Generate plan and go to dashboard
      setLoading(true);
      try {
        if (!planGenerated && householdId) {
          await generatePlan();
          setPlanGenerated(true);
        }
        router.push("/dashboard");
      } catch {
        router.push("/dashboard");
      } finally {
        setLoading(false);
      }
      return;
    }

    setStep(step + 1);
  }

  // ─── Member helpers ────────────────────────────────────────────────────

  function addMemberRow() {
    if (members.length >= 8) return;
    setMembers([...members, { name: "", age: null }]);
  }

  function removeMemberRow(idx: number) {
    if (members.length <= 1) return;
    setMembers(members.filter((_, i) => i !== idx));
  }

  function updateMember(idx: number, field: "name" | "age", value: string) {
    const updated = [...members];
    if (field === "name") {
      updated[idx].name = value;
    } else {
      updated[idx].age = value ? parseInt(value) : null;
    }
    setMembers(updated);
  }

  // ─── Dietary helpers ────────────────────────────────────────────────────

  function toggleDietType(t: DietType) {
    if (dietTypes.includes(t)) {
      setDietTypes(dietTypes.filter((d) => d !== t));
    } else {
      setDietTypes([...dietTypes, t]);
    }
  }

  function toggleAllergy(a: Allergy) {
    if (allergies.includes(a)) {
      setAllergies(allergies.filter((x) => x !== a));
    } else {
      setAllergies([...allergies, a]);
    }
  }

  function toggleCuisine(c: Cuisine) {
    if (cuisines.includes(c)) {
      setCuisines(cuisines.filter((x) => x !== c));
    } else {
      setCuisines([...cuisines, c]);
    }
  }

  function selectedDietSummary(): string {
    if (dietTypes.length === 0) return "Nicht ausgewählt";
    return dietTypes.map((d) => DIET_LABELS[d]).join(", ");
  }

  function selectedAllergySummary(): string {
    if (allergies.length === 0) return "Keine";
    return allergies.map((a) => ALLERGY_LABELS[a]).join(", ");
  }

  function selectedCuisineSummary(): string {
    if (cuisines.length === 0) return "Keine Präferenz";
    return cuisines.map((c) => CUISINE_LABELS[c]).join(", ");
  }

  function memberSummary(): string {
    const valid = members.filter((m) => m.name.trim().length > 0);
    if (valid.length === 0) return "–";
    return valid.map((m) => {
      const ageStr = m.age ? ` (${m.age} J.)` : "";
      return `${m.name}${ageStr}`;
    }).join(", ");
  }

  // ─── Render ────────────────────────────────────────────────────────────

  return (
    <section className="mx-auto max-w-[720px] px-6 py-12">
      {/* Progress bar */}
      <div className="mb-6 flex items-center gap-3">
        <span className="text-xs font-bold text-sprossa-green">Schritt {step + 1} von {TOTAL_STEPS}</span>
        <div className="h-2 flex-1 rounded-full bg-sprossa-muted/20 overflow-hidden">
          <div
            className="h-full rounded-full bg-sprossa-green transition-all duration-300"
            style={{ width: `${progressPercent()}%` }}
          />
        </div>
      </div>

      <h1 className="mb-6 font-display text-[28px] text-sprossa-ink">{stepTitle()}</h1>

      {/* ═══ Step 0: Household ═══ */}
      {step === 0 && (
        <div className="space-y-4">
          <p className="mb-4 text-sprossa-muted">
            Wie heißt euer Haushalt? Das kann der Familienname sein oder ein Spitzname – ganz euch überlassen.
          </p>
          <input
            type="text"
            value={householdName}
            onChange={(e) => setHouseholdName(e.target.value)}
            className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink text-lg"
            placeholder="z.B. Familie Mustermann"
            required
          />
        </div>
      )}

      {/* ═══ Step 1: Members ═══ */}
      {step === 1 && (
        <div className="space-y-4">
          <p className="mb-4 text-sprossa-muted">
            Wer lebt in eurem Haushalt? Trag alle ein, die mitessen (min. 1, max. 8).
          </p>

          {members.map((m, idx) => (
            <div
              key={`member-${idx}`}
              className="flex items-center gap-3 rounded-xl border border-sprossa-ink/10 bg-white p-4"
            >
              <span className="font-bold text-sprossa-ink text-sm">{idx + 1}.</span>
              <input
                type="text"
                value={m.name}
                onChange={(e) => updateMember(idx, "name", e.target.value)}
                className="flex-1 rounded-lg border border-sprossa-muted/20 px-3 py-2 text-sprossa-ink"
                placeholder="Name"
              />
              <input
                type="number"
                value={m.age ?? ""}
                onChange={(e) => updateMember(idx, "age", e.target.value)}
                className="w-20 rounded-lg border border-sprossa-muted/20 px-3 py-2 text-sprossa-ink"
                placeholder="Alter"
                min={0}
                max={120}
              />
              {members.length > 1 && (
                <button
                  onClick={() => removeMemberRow(idx)}
                  className="rounded-lg bg-sprossa-error/10 px-3 py-2 text-sm text-sprossa-error font-bold"
                >
                  ✕
                </button>
              )}
            </div>
          ))}

          {members.length < 8 && (
            <button
              onClick={addMemberRow}
              className="w-full rounded-xl border-2 border-dashed border-sprossa-green/40 px-4 py-3 font-bold text-sprossa-green hover:bg-sprossa-sage transition-colors"
            >
              + Mitglied hinzufügen
            </button>
          )}

          <p className="text-xs text-sprossa-muted">
            {members.length}/8 Mitglieder
          </p>
        </div>
      )}

      {/* ═══ Step 2: Diet + Allergies + Cuisines + Dislikes ═══ */}
      {step === 2 && (
        <div className="space-y-6">
          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Esst ihr…</h2>
            <p className="mb-3 text-sm text-sprossa-muted">Alles zutreffende auswählen.</p>
            <div className="flex flex-wrap gap-3">
              {(["fleisch", "fisch", "vegetarisch", "vegan"] as DietType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => toggleDietType(t)}
                  className={`rounded-xl border-2 px-4 py-3 font-bold text-sm transition-all ${
                    dietTypes.includes(t)
                      ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green"
                      : "border-sprossa-muted/20 bg-white text-sprossa-muted"
                  }`}
                >
                  {DIET_LABELS[t]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">Allergien & Unverträglichkeiten</h2>
            <p className="mb-3 text-sm text-sprossa-muted">Falls vorhanden – alles gut, wenn nicht.</p>
            <div className="flex flex-wrap gap-3">
              {(["gluten", "laktose", "nüsse", "ei", "soja"] as Allergy[]).map((a) => (
                <button
                  key={a}
                  onClick={() => toggleAllergy(a)}
                  className={`rounded-xl border-2 px-4 py-3 font-bold text-sm transition-all ${
                    allergies.includes(a)
                      ? "border-sprossa-terracotta bg-sprossa-terracotta/10 text-sprossa-terracotta"
                      : "border-sprossa-muted/20 bg-white text-sprossa-muted"
                  }`}
                >
                  {ALLERGY_LABELS[a]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">🍳 Küchen-Präferenzen</h2>
            <p className="mb-3 text-sm text-sprossa-muted">Welche Küchenrichtungen mögt ihr? (Mehrfachauswahl)</p>
            <div className="flex flex-wrap gap-3">
              {(["deutsch", "italienisch", "asiatisch", "orientalisch", "mexikanisch"] as Cuisine[]).map((c) => (
                <button
                  key={c}
                  onClick={() => toggleCuisine(c)}
                  className={`rounded-xl border-2 px-4 py-3 font-bold text-sm transition-all ${
                    cuisines.includes(c)
                      ? "border-sprossa-green bg-sprossa-green/10 text-sprossa-green"
                      : "border-sprossa-muted/20 bg-white text-sprossa-muted"
                  }`}
                >
                  {CUISINE_LABELS[c]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">🚫 Was isst du nicht?</h2>
            <p className="mb-3 text-sm text-sprossa-muted">Kommasepariert, z.B. „Pilze, Innereien, Rote Bete"</p>
            <input
              type="text"
              value={dislikedIngredients}
              onChange={(e) => setDislikedIngredients(e.target.value)}
              className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
              placeholder="Pilze, Innereien, Rote Bete"
            />
          </div>
        </div>
      )}

      {/* ═══ Step 3: Shopping habits ═══ */}
      {step === 3 && (
        <div className="space-y-6">
          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">🏪 Wo kauft ihr ein?</h2>
            <div className="space-y-3">
              {SUPERMARKET_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-center gap-4 rounded-xl border-2 p-4 cursor-pointer transition-all ${
                    supermarket === opt.value
                      ? "border-sprossa-green bg-sprossa-green/5"
                      : "border-sprossa-muted/20 bg-white"
                  }`}
                >
                  <input
                    type="radio"
                    name="supermarket"
                    value={opt.value}
                    checked={supermarket === opt.value}
                    onChange={() => setSupermarket(opt.value)}
                    className="size-5 accent-sprossa-green"
                  />
                  <span className="font-bold text-sprossa-ink">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">💰 Monatliches Budget</h2>
            <p className="mb-3 text-sm text-sprossa-muted">Was gebt ihr monatlich für Lebensmittel aus?</p>
            <div className="space-y-3">
              {BUDGET_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-center gap-4 rounded-xl border-2 p-4 cursor-pointer transition-all ${
                    budgetRange === opt.value
                      ? "border-sprossa-terracotta bg-sprossa-terracotta/5"
                      : "border-sprossa-muted/20 bg-white"
                  }`}
                >
                  <input
                    type="radio"
                    name="budgetRange"
                    value={opt.value}
                    checked={budgetRange === opt.value}
                    onChange={() => setBudgetRange(opt.value)}
                    className="size-5 accent-sprossa-green"
                  />
                  <span className="font-bold text-sprossa-ink">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-2 font-display text-lg font-semibold text-sprossa-ink">🛍️ Wie oft kauft ihr ein?</h2>
            <div className="space-y-3">
              {FREQUENCY_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-center gap-4 rounded-xl border-2 p-4 cursor-pointer transition-all ${
                    shoppingFrequency === opt.value
                      ? "border-sprossa-green bg-sprossa-green/5"
                      : "border-sprossa-muted/20 bg-white"
                  }`}
                >
                  <input
                    type="radio"
                    name="shoppingFrequency"
                    value={opt.value}
                    checked={shoppingFrequency === opt.value}
                    onChange={() => setShoppingFrequency(opt.value)}
                    className="size-5 accent-sprossa-green"
                  />
                  <span className="font-bold text-sprossa-ink">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ═══ Step 4: Time budget ═══ */}
      {step === 4 && (
        <div>
          <p className="mb-6 text-sprossa-muted">
            Wie viel Zeit habt ihr abends zum Kochen? Das hilft uns, passende Rezepte auszuwählen.
          </p>
          <div className="space-y-3">
            {TIME_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className={`flex items-center gap-4 rounded-xl border-2 p-4 cursor-pointer transition-all ${
                  timeBudget === opt.value
                    ? "border-sprossa-green bg-sprossa-green/5"
                    : "border-sprossa-muted/20 bg-white"
                }`}
              >
                <input
                  type="radio"
                  name="timeBudget"
                  value={opt.value}
                  checked={timeBudget === opt.value}
                  onChange={() => setTimeBudget(opt.value)}
                  className="size-5 accent-sprossa-green"
                />
                <div className="flex-1">
                  <span className="font-bold text-sprossa-ink">{opt.label}</span>
                  <p className="text-sm text-sprossa-muted">{opt.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* ═══ Step 5: Done! ═══ */}
      {step === 5 && (
        <div className="text-center">
          <div className="mb-6 text-6xl">🎉</div>
          <h2 className="mb-4 font-display text-2xl font-bold text-sprossa-green">
            Fertig! Euer Sprossa-Konto ist bereit.
          </h2>
          <p className="mb-8 text-sprossa-muted">
            Hier ist eine Zusammenfassung – ihr könnt alles später im Profil anpassen.
          </p>

          <div className="mb-8 rounded-xl border border-sprossa-ink/10 bg-white p-6 text-left">
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Haushalt</td>
                  <td className="py-2 text-sprossa-ink">{householdName}</td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Mitglieder</td>
                  <td className="py-2 text-sprossa-ink">{memberSummary()}</td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Ess-Typ</td>
                  <td className="py-2 text-sprossa-ink">{selectedDietSummary()}</td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Allergien</td>
                  <td className="py-2 text-sprossa-ink">{selectedAllergySummary()}</td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Küchen-Präferenzen</td>
                  <td className="py-2 text-sprossa-ink">{selectedCuisineSummary()}</td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Abneigungen</td>
                  <td className="py-2 text-sprossa-ink">{dislikedIngredients || "Keine"}</td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Supermarkt</td>
                  <td className="py-2 text-sprossa-ink">
                    {(() => { const o = SUPERMARKET_OPTIONS.find((o) => o.value === supermarket); return o ? o.label : "–"; })()}
                  </td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Monatsbudget</td>
                  <td className="py-2 text-sprossa-ink">
                    {(() => { const o = BUDGET_OPTIONS.find((o) => o.value === budgetRange); return o ? o.label : "–"; })()}
                  </td>
                </tr>
                <tr className="border-b border-sprossa-ink/10">
                  <td className="py-2 font-semibold text-sprossa-muted">Einkaufs-Rhythmus</td>
                  <td className="py-2 text-sprossa-ink">
                    {(() => { const o = FREQUENCY_OPTIONS.find((o) => o.value === shoppingFrequency); return o ? o.label : "–"; })()}
                  </td>
                </tr>
                <tr>
                  <td className="py-2 font-semibold text-sprossa-muted">Zeitbudget</td>
                  <td className="py-2 text-sprossa-ink">
                    {(() => { const o = TIME_OPTIONS.find((o) => o.value === timeBudget); return o ? o.label : "–"; })()}
                  </td>
                </tr>
              </tbody>
            </table>

            {planResult && (
              <div className="mt-4 rounded-lg bg-sprossa-sage p-3 text-sm font-medium text-sprossa-dark">
                {planResult}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
          {error}
        </div>
      )}

      {/* Navigation */}
      <div className="mt-8 flex items-center justify-between gap-4">
        <button
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
          className="rounded-xl border border-sprossa-muted/30 px-5 py-3 text-sprossa-ink font-bold disabled:opacity-40"
        >
          ← Zurück
        </button>

        <button
          onClick={handleNext}
          disabled={loading || !canProceed()}
          className="rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark disabled:opacity-60"
        >
          {loading ? "Wird gespeichert…" : nextStepLabel()}
        </button>
      </div>
    </section>
  );
}
