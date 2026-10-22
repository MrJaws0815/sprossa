"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const TOKEN_KEY = "sprossa_token";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setSuccess("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const msg = await res.json().catch(() => ({}));
        if (res.status === 401) {
          throw new Error("E-Mail oder Passwort falsch.");
        }
        throw new Error((msg as any).detail || "Login fehlgeschlagen");
      }

      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setSuccess("✅ Login erfolgreich! Weiterleitung…");
      setTimeout(() => router.push("/dashboard"), 800);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function demoLogin(email: string, password: string) {
    setEmail(email); setPassword(password); setError(""); setSuccess("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Demo-Login fehlgeschlagen");
      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setSuccess("✅ Demo-Zugang aktiviert! Weiterleitung…");
      setTimeout(() => router.push("/dashboard"), 800);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto max-w-[720px] px-6 py-16">
      <div className="text-center mb-10">
        <span className="inline-flex items-center gap-3 mb-6">
          <span className="size-[48px] rounded-[14px] bg-sprossa-green grid place-items-center text-2xl">🌱</span>
        </span>
        <h1 className="font-display text-[36px] font-bold text-sprossa-ink mb-3">
          Willkommen zurück
        </h1>
        <p className="text-lg text-sprossa-muted mb-2">
          Schön, dass du wieder da bist. Dein nächster Monatsplan wartet.
        </p>
      </div>

      <div className="rounded-xl border border-sprossa-ink/10 bg-white p-8 shadow-[0_8px_24px_rgba(38,48,43,0.06)] max-w-md mx-auto">
        <h2 className="font-display text-xl font-semibold text-sprossa-ink mb-6">Anmelden</h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-1 block text-sm font-semibold text-sprossa-ink">E-Mail</label>
            <input type="email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
              placeholder="ich@familie.de" required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold text-sprossa-ink">Passwort</label>
            <input type="password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
              placeholder="******" required minLength={8} />
          </div>

          {error && (
            <div className="rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
              ❌ {error}
            </div>
          )}
          {success && (
            <div className="rounded-lg bg-sprossa-sage p-3 text-sm text-sprossa-dark font-medium">
              {success}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark disabled:opacity-60 text-lg">
            {loading ? "👤 Wird eingeloggt…" : "👤 Anmelden"}
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-sprossa-muted">
          Noch kein Konto? <a href="/register" className="text-sprossa-green font-semibold">Registrieren</a>
        </div>
      </div>

      <div className="mt-8 text-center max-w-md mx-auto rounded-xl border border-dashed border-sprossa-amber/30 bg-sprossa-sage p-6">
        <h3 className="font-display text-lg font-semibold text-sprossa-ink">🎮 Demo-Zugang</h3>
        <p className="text-sm text-sprossa-muted mt-2">
          Kein Konto? Kein Problem. Starte direkt mit einem Demo-Account.
        </p>
        <button onClick={() => demoLogin("demo@sprossa.de", "demo1234")}
          className="mt-4 rounded-xl bg-sprossa-amber px-6 py-3 font-bold text-white hover:brightness-110">
          🚀 Demo starten
        </button>
        <p className="mt-2 text-xs text-sprossa-muted">
          ⚡ Demo-Daten werden automatisch geladen
        </p>
      </div>

      <div className="mt-12 text-center">
        <div className="flex flex-wrap justify-center gap-6 text-sm text-sprossa-muted">
          <span>🔒 DSGVO-konform</span>
          <span>🇪🇺 Deutsche Server (Hetzner)</span>
          <span>💳 Keine Zahlungsdaten nötig</span>
        </div>
      </div>
    </section>
  );
}