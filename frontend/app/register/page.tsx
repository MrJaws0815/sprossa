"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
const TOKEN_KEY = "sprossa_token";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [name, setName] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");

    if (confirm !== password) { setMsg("❌ Passwörter stimmen nicht überein"); return; }
    if (password.length < 8) { setMsg("❌ Mindestens 8 Zeichen"); return; }

    setLoading(true);
    try {
      const r = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, display_name: name }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        if (r.status === 409) {
          setMsg("❌ E-Mail bereits registriert – <a href='/login' class='font-semibold text-sprossa-green'>zum Login</a>");
          return;
        }
        setMsg("❌ " + ((d as any).detail || "Fehler"));
        return;
      }
      const d = await r.json();
      localStorage.setItem(TOKEN_KEY, d.access_token);
      window.location.href = "/onboarding";
    } catch (e: any) {
      setMsg("❌ " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md mt-16 px-4">
      <h1 className="font-display text-3xl font-bold text-sprossa-ink mb-1">Konto erstellen</h1>
      <p className="mb-8 text-sprossa-muted">In 2 Minuten hast du deinen ersten Monatsplan.</p>

      <form onSubmit={handleSubmit} className="space-y-4 w-full">
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Anzeigename</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="z.B. Familie Mustermann" required />
        </div>
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">E-Mail</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="ich@familie.de" required />
        </div>
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Passwort</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="Mindestens 8 Zeichen" required minLength={8} />
        </div>
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Passwort wiederholen</label>
          <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="******" required />
        </div>

        {msg && (
          <div className="rounded-lg border border-sprossa-error/20 bg-sprossa-error/5 px-4 py-3 text-sm text-sprossa-error font-medium">
            <span dangerouslySetInnerHTML={{ __html: msg }} />
          </div>
        )}

        <button type="submit" disabled={loading}
          className="w-full rounded-xl bg-sprossa-green px-4 py-3 font-bold text-white text-base hover:bg-sprossa-dark disabled:opacity-60">
          {loading ? "Einen Moment …" : "Konto erstellen"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center text-sprossa-muted">
        Bereits registriert? <a href="/login" className="font-semibold text-sprossa-green underline">Anmelden</a>
      </p>
    </div>
  );
}