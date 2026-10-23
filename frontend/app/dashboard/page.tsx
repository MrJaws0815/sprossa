"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authHeaders, getApiBase } from "../lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState({ recipes: 0, weeksPlanned: 0, groceryItems: 0 });
  const [planCount, setPlanCount] = useState(0);
  const [weeklyMeals, setWeeklyMeals] = useState<{ day: string; meal: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const headers = authHeaders();

      const recipesRes = await fetch(`${getApiBase()}/recipes`, { headers });
      if (recipesRes.ok) {
        const recipes = await recipesRes.json();
        setStats((s) => ({ ...s, recipes: recipes.length }));
      }

      const plansRes = await fetch(`${getApiBase()}/plans`, { headers });
      if (plansRes.ok) {
        const plans = await plansRes.json();
        setPlanCount(plans.length);
        setStats((s) => ({ ...s, weeksPlanned: plans.length * 4 }));

        if (plans.length > 0) {
          const weeksRes = await fetch(`${getApiBase()}/plans/${plans[0].id}/weeks`, { headers });
          if (weeksRes.ok) {
            const weeks = await weeksRes.json();
            if (weeks.length > 0) {
              const slots = weeks[0].meal_slots || [];
              const dayNames = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];
              setWeeklyMeals(
                slots.map((s: any) => ({
                  day: dayNames[s.day_of_week - 1] || `Tag ${s.day_of_week}`,
                  meal: "🍽 Rezept",
                }))
              );
            }
          }
        }
      }

      const groceryRes = await fetch(`${getApiBase()}/grocery-lists`, { headers });
      if (groceryRes.ok) {
        const lists = await groceryRes.json();
        const total = lists.reduce((acc: number, l: any) => acc + (l.items?.length || 0), 0);
        setStats((s) => ({ ...s, groceryItems: total }));
      }
    } catch (e) {
      setStats({ recipes: 0, weeksPlanned: 0, groceryItems: 0 });
      setError("Dashboard-Daten konnten nicht geladen werden");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <section className="py-8">
      <div className="grid gap-4 md:grid-cols-3 p-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-sprossa-muted/10 rounded-xl h-24" />
        ))}
      </div>
    </section>
  );

  // Error-State (API-Fehler)
  if (error) {
    return (
      <section className="py-8">
        <div className="mx-auto max-w-lg rounded-xl border border-sprossa-error/30 bg-white p-8 text-center">
          <p className="mb-4 text-xl text-sprossa-error font-bold">Dashboard-Daten konnten nicht geladen werden</p>
          <p className="mb-6 text-sm text-sprossa-muted">Bitte ueberpruefe deine Internetverbindung und versuche es erneut.</p>
          <button onClick={() => { setError(""); setLoading(true); loadDashboard(); }}
            className="rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark">
            Erneut versuchen
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold text-sprossa-ink">📊 Dashboard</h1>
        <div className="flex gap-3">
          <Link href="/dashboard/profile" className="rounded-lg border border-sprossa-green px-4 py-2 text-sm text-sprossa-green">
            👤 Profil
          </Link>
          <button
            onClick={() => { fetch(`${getApiBase()}/auth/logout`, { method: "POST" }).finally(() => router.push("/login")); }}
            className="rounded-lg border border-sprossa-error px-4 py-2 text-sm text-sprossa-error"
          >
            🚪 Logout
          </button>
        </div>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-3">
        <a href="/dashboard/recipes" className="group rounded-xl border border-sprossa-ink/10 bg-white p-5 text-center transition-all hover:shadow-md hover:border-sprossa-green/40 cursor-pointer">
          <div className="mb-1 text-3xl">📖</div>
          <div className="mb-1 font-display text-2xl font-bold text-sprossa-ink group-hover:text-sprossa-green transition-colors">{stats.recipes}</div>
          <div className="text-sm text-sprossa-muted">Rezepte</div>
        </a>
        <a href="/dashboard/plan" className="group rounded-xl border border-sprossa-ink/10 bg-white p-5 text-center transition-all hover:shadow-md hover:border-sprossa-green/40 cursor-pointer">
          <div className="mb-1 text-3xl">📅</div>
          <div className="mb-1 font-display text-2xl font-bold text-sprossa-ink group-hover:text-sprossa-green transition-colors">{planCount}</div>
          <div className="text-sm text-sprossa-muted">Monatspläne</div>
        </a>
        <a href="/dashboard/grocery" className="group rounded-xl border border-sprossa-ink/10 bg-white p-5 text-center transition-all hover:shadow-md hover:border-sprossa-green/40 cursor-pointer">
          <div className="mb-1 text-3xl">🛒</div>
          <div className="mb-1 font-display text-2xl font-bold text-sprossa-ink group-hover:text-sprossa-green transition-colors">{stats.groceryItems}</div>
          <div className="text-sm text-sprossa-muted">Einkaufs-Items</div>
        </a>
      </div>

      {/* Empty-State: noch kein Monatsplan */}
      {planCount === 0 && (
        <div className="mb-8 rounded-xl border border-sprossa-ink/10 bg-sprossa-sage p-6 text-center">
          <p className="text-lg font-semibold text-sprossa-ink">
            📅 Noch kein Monatsplan –{" "}
            <a href="/dashboard/plan" className="text-sprossa-green font-bold underline hover:text-sprossa-dark">
              ersten Plan erstellen
            </a>
          </p>
        </div>
      )}

      <div className="mb-8 rounded-xl border border-sprossa-ink/10 bg-white p-6">
        <h2 className="mb-4 font-display text-xl font-semibold text-sprossa-ink">📅 Wochenvorschau</h2>
        <div className="grid gap-3">
          {["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"].map((day) => {
            const meal = weeklyMeals.find((m) => m.day === day);
            return (
              <div key={day} className="flex items-center justify-between border-b border-sprossa-ink/10 pb-2">
                <span className="font-medium text-sprossa-ink">{day}</span>
                <span className="text-sm text-sprossa-muted">{meal ? meal.meal : "📅 Noch kein Plan"}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap justify-center gap-4">
        <Link href="/dashboard/plan" className="rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark">
          📅 Monatsplan ansehen
        </Link>
        <Link href="/dashboard/grocery" className="rounded-xl border border-sprossa-green px-6 py-3 font-bold text-sprossa-green hover:bg-sprossa-sage">
          🛒 Einkaufsliste
        </Link>
        <Link href="/dashboard/recipes" className="rounded-xl border border-sprossa-muted/30 px-6 py-3 font-bold text-sprossa-ink hover:bg-sprossa-sage">
          📖 Rezepte
        </Link>
      </div>
    </section>
  );
}

function KpiCard({ label, value, icon }: { label: string; value: number; icon: string }) {
  return (
    <div className="rounded-xl border border-sprossa-ink/10 bg-white p-5 text-center">
      <div className="mb-1 text-3xl">{icon}</div>
      <div className="mb-1 font-display text-2xl font-bold text-sprossa-ink">{value}</div>
      <div className="text-sm text-sprossa-muted">{label}</div>
    </div>
  );
}
