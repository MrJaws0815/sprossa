"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(""); setLoading(true);
    try {
      const r = await fetch(`${API}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const d = await r.json().catch(() => ({}));
      setMsg("✅ " + (d as any).message || "Wenn die E-Mail existiert, erhältst du einen Link zum Zurücksetzen.");
    } catch (e: any) {
      setMsg("❌ " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md mt-16 px-4">
      <h1 className="font-display text-3xl font-bold text-sprossa-ink mb-1">Passwort vergessen</h1>
      <p className="mb-8 text-sprossa-muted">Gib deine E-Mail-Adresse ein, um einen Reset-Link zu erhalten.</p>

      <form onSubmit={handleSubmit} className="space-y-4 w-full">
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">E-Mail</label>
          <input type="email" value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="ich@familie.de" required />
        </div>

        {msg && (
          <div className="rounded-lg border border-sprossa-green/20 bg-sprossa-sage px-4 py-3 text-sm text-sprossa-ink font-medium">
            <span dangerouslySetInnerHTML={{ __html: msg }} />
          </div>
        )}

        <button type="submit" disabled={loading}
          className="w-full rounded-xl bg-sprossa-green px-4 py-3 font-bold text-white text-base hover:bg-sprossa-dark disabled:opacity-60">
          {loading ? "Einen Moment …" : "Link anfordern"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center text-sprossa-muted">
        Zurück zum <a href="/login" className="font-semibold text-sprossa-green underline">Login</a>
      </p>
    </div>
  );
}