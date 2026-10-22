"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const TOKEN_KEY = "sprossa_token";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@sprossa.de");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const msg = await res.json().catch(() => ({}));
        throw new Error((msg as any).detail || "Login fehlgeschlagen");
      }

      const data = await res.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto max-w-[1080px] px-6 py-12">
      <h1 className="mb-2 font-display text-[32px] text-sprossa-ink">Anmelden</h1>
      <p className="mb-8 text-sprossa-muted">Mit deinem Sprossa-Konto einloggen.</p>

      <form onSubmit={handleSubmit} className="mx-auto max-w-sm space-y-4">
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
          {loading ? "Wird gesendet…" : "Anmelden"}
        </button>

        <p className="text-center text-xs text-sprossa-muted">
          Demo: <strong>demo@sprossa.de</strong> / <strong>demo1234</strong>
        </p>
      </form>
    </section>
  );
}