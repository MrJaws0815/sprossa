"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@sprossa.de");
  const [password, setPassword] = useState("demo1234");
  const [showPassword, setShowPassword] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setMsg(""); setLoading(true);
    try {
      const r = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setMsg("❌ " + ((d as any).detail || "Falsche E-Mail oder Passwort"));
        return; // ← setLoading(false) in finally
      }
      const d = await r.json();
      window.location.href = "/dashboard"; // ← redirect via location statt router
    } catch (e: any) {
      setMsg("❌ " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md mt-16 px-4">
      <h1 className="font-display text-3xl font-bold text-sprossa-ink mb-1">Anmelden</h1>
      <p className="mb-8 text-sprossa-muted">Gib deine Daten ein, um fortzufahren.</p>

      <form onSubmit={handleLogin} className="space-y-4 w-full">
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">E-Mail</label>
          <input type="email" value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="ich@familie.de" required />
        </div>
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Passwort</label>
          <div className="relative">
            <input type={showPassword ? "text" : "password"} value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 pr-12 text-sprossa-ink text-base"
              placeholder="******" required minLength={8} />
            <button type="button" onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 flex items-center px-3 text-lg cursor-pointer"
              aria-label={showPassword ? "Passwort verbergen" : "Passwort anzeigen"}>
              {showPassword ? "🙈" : "👁"}
            </button>
          </div>
        </div>

        {msg && (
          <div className="rounded-lg border border-sprossa-error/20 bg-sprossa-error/5 px-4 py-3 text-sm text-sprossa-error font-medium">
            {msg}
          </div>
        )}

        <div className="text-right mt-1">
          <a href="/forgot-password" className="text-sm text-sprossa-muted underline">Passwort vergessen?</a>
        </div>

        <button type="submit" disabled={loading}
          className="w-full rounded-xl bg-sprossa-green px-4 py-3 font-bold text-white text-base hover:bg-sprossa-dark disabled:opacity-60">
          {loading ? "Einen Moment …" : "Anmelden"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center text-sprossa-muted">
        Noch kein Konto? <a href="/register" className="font-semibold text-sprossa-green underline">Registrieren</a>
      </p>

      <div className="mt-8 rounded-xl border-2 border-dashed border-sprossa-green/20 bg-sprossa-sage p-4">
        <h2 className="font-semibold text-sprossa-dark text-base">Demo-Zugang</h2>
        <p className="text-xs text-sprossa-muted mt-1">Demo-Daten sind bereits eingetragen. Einfach auf <strong>Anmelden</strong> klicken.</p>
      </div>
    </div>
  );
}