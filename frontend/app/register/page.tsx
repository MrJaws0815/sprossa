"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const TOKEN_KEY = "sprossa_token";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [dsgvo, setDsgvo] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setSuccess("");

    if (password !== confirmPassword) {
      setError("Die Passwörter stimmen nicht überein.");
      return;
    }
    if (password.length < 8) {
      setError("Das Passwort muss mindestens 8 Zeichen lang sein.");
      return;
    }
    if (!dsgvo) {
      setError("Bitte stimme der Datenschutzerklärung zu.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, display_name: displayName }),
      });

      if (!res.ok) {
        const msg = await res.json().catch(() => ({}));
        if (res.status === 409) {
          throw new Error("Diese E-Mail ist bereits registriert. <a href='/login' class='text-sprossa-green font-semibold'>Zum Login</a>");
        }
        throw new Error((msg as any).detail || "Registrierung fehlgeschlagen");
      }

      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setSuccess("✅ Konto erstellt! Weiterleitung zum Onboarding…");
      setTimeout(() => router.push("/onboarding"), 800);
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
          Sprossa-Konto erstellen
        </h1>
        <p className="text-lg text-sprossa-muted mb-2">
          In 2 Minuten hast du deinen ersten Monatsplan. Kostenlos, unverbindlich.
        </p>
      </div>

      <div className="rounded-xl border border-sprossa-ink/10 bg-white p-8 shadow-[0_8px_24px_rgba(38,48,43,0.06)] max-w-md mx-auto">
        <h2 className="font-display text-xl font-semibold text-sprossa-ink mb-6">Registrieren</h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-1 block text-sm font-semibold text-sprossa-ink">Anzeigename</label>
            <input type="text" value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
              placeholder="z.B. Familie Mustermann" required />
          </div>
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
              placeholder="Mindestens 8 Zeichen" required minLength={8} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold text-sprossa-ink">Passwort wiederholen</label>
            <input type="password" value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
              placeholder="******" required />
          </div>

          <label className="flex gap-3 items-start text-sm leading-relaxed text-sprossa-muted">
            <input type="checkbox" checked={dsgvo}
              onChange={(e) => setDsgvo(e.target.checked)}
              className="mt-1 size-5 shrink-0 accent-sprossa-green" required />
            <span>
              Ich bin mit der Verarbeitung meiner Daten gemäß der{" "}
              <a href="/datenschutz" target="_blank" className="text-sprossa-green underline">Datenschutzerklärung</a>{" "}
              einverstanden.
            </span>
          </label>

          {error && (
            <div className="rounded-lg bg-sprossa-error/10 border border-sprossa-error p-3 text-sm text-sprossa-error font-medium">
              ❌ <span dangerouslySetInnerHTML={{ __html: error }} />
            </div>
          )}
          {success && (
            <div className="rounded-lg bg-sprossa-sage p-3 text-sm text-sprossa-dark font-medium">
              {success}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full rounded-xl bg-sprossa-green px-6 py-3 font-bold text-white hover:bg-sprossa-dark disabled:opacity-60 text-lg">
            {loading ? "🌱 Wird erstellt…" : "🌱 Kostenloses Konto erstellen"}
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-sprossa-muted">
          Bereits registriert? <a href="/login" className="text-sprossa-green font-semibold">Anmelden</a>
        </div>
      </div>

      <div className="mt-12 text-center">
        <div className="grid grid-cols-3 gap-6 text-sm text-sprossa-muted">
          <div className="text-center">
            <div className="text-2xl mb-2">🆓</div>
            <div className="font-semibold text-sprossa-ink">Kostenlos</div>
            <div className="text-xs">Keine Zahlungsdaten. Kein Risiko.</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-2">⚡</div>
            <div className="font-semibold text-sprossa-ink">Sofort loslegen</div>
            <div className="text-xs">Onboarding in 2 Minuten. Erster Plan sofort.</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-2">🔒</div>
            <div className="font-semibold text-sprossa-ink">DSGVO-konform</div>
            <div className="text-xs">Deutsche Server (Hetzner). Deine Daten, dein Plan.</div>
          </div>
        </div>
      </div>
    </section>
  );
}