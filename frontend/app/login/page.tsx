"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const TOKEN_KEY = "sprossa_token";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@sprossa.de");
  const [password, setPassword] = useState("demo1234");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setMsg(""); setLoading(true);
    try {
      const r = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setMsg("❌ " + ((d as any).detail || "Falsche E-Mail oder Passwort"));
        setLoading(false); return;
      }
      const d = await r.json();
      localStorage.setItem(TOKEN_KEY, d.access_token);
      router.push("/dashboard");
    } catch (e: any) {
      setMsg("❌ " + e.message);
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
          <input type="password" value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="******" required minLength={8} />
        </div>

        {msg && (
          <div className="rounded-lg border border-sprossa-error/20 bg-sprossa-error/5 px-4 py-3 text-sm text-sprossa-error font-medium">
            {msg}
          </div>
        )}

        <button type="submit" disabled={loading}
          className="w-full rounded-xl bg-sprossa-green px-4 py-3 font-bold text-white text-base hover:bg-sprossa-dark disabled:opacity-60">
          {loading ? "Bitte warten …" : "Anmelden"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center text-sprossa-muted">
        Noch kein Konto? <a href="/register" className="font-semibold text-sprossa-green underline">Registrieren</a>
      </p>

      <div className="mt-8 rounded-xl border-2 border-dashed border-sprossa-green/20 bg-sprossa-sage p-4">
        <h2 className="font-semibold text-sprossa-dark text-base">Demo-Zugang</h2>
        <p className="text-xs text-sprossa-muted mt-1">Die Felder oben sind bereits mit den Demo-Daten vorausgefüllt. Klick einfach auf „Anmelden".</p>
        <p className="text-xs text-sprossa-muted mt-1">Du kannst auch eine <a href="/register" className="text-sprossa-green underline">eigene Registrierung</a> anlegen.</p>
      </div>
    </div>
  );
}