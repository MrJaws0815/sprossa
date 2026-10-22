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
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Die Passwörter stimmen nicht überein.");
      return;
    }
    if (password.length < 8) {
      setError("Das Passwort muss mindestens 8 Zeichen lang sein.");
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
          throw new Error("Diese E-Mail ist bereits registriert.");
        }
        throw new Error((msg as any).detail || "Registrierung fehlgeschlagen");
      }

      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      router.push("/onboarding");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto max-w-[1080px] px-6 py-12">
      <h1 className="mb-2 font-display text-[32px] text-sprossa-ink">Konto erstellen</h1>
      <p className="mb-8 text-sprossa-muted">
        Erstelle dein Sprossa-Konto und leg los.
      </p>

      <form onSubmit={handleSubmit} className="mx-auto max-w-sm space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-sprossa-ink">Anzeigename</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
            placeholder="z.B. Familie Mustermann"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-sprossa-ink">E-Mail</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
            placeholder="ich@familie.de"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-sprossa-ink">Passwort</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
            placeholder="******"
            minLength={8}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-sprossa-ink">Passwort wiederholen</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full rounded-xl border border-sprossa-muted/20 px-4 py-3 text-sprossa-ink"
            placeholder="******"
            required
          />
        </div>

        {error && (
          <p className="text-sm text-sprossa-error">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-sprossa-green px-4 py-3 font-bold text-white hover:bg-sprossa-dark disabled:opacity-60"
        >
          {loading ? "Wird gesendet…" : "Konto erstellen"}
        </button>

        <p className="text-center text-sm text-sprossa-muted">
          Bereits registriert?{" "}
          <a href="/login" className="text-sprossa-green font-semibold">Anmelden</a>
        </p>
      </form>
    </section>
  );
}