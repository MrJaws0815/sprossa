"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [name, setName] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [accepted, setAccepted] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");

    if (confirm !== password) { setMsg("❌ Passwörter stimmen nicht überein"); return; }
    if (password.length < 8) { setMsg("❌ Mindestens 8 Zeichen"); return; }
    if (!accepted) { setMsg("❌ Bitte AGB und Datenschutz akzeptieren"); return; }

    setLoading(true);
    try {
      const r = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, display_name: name, accepted_terms: accepted }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        if (r.status === 409) {
          setMsg("❌ E-Mail bereits registriert – bitte zum Login wechseln");
          return;
        }
        setMsg("❌ " + ((d as any).detail || "Fehler"));
        return;
      }
      const d = await r.json();
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
          <div className="relative">
            <input type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
              className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 pr-12 text-sprossa-ink text-base"
              placeholder="Mindestens 8 Zeichen" required minLength={8} />
            <button type="button" onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 flex items-center px-3 text-lg cursor-pointer"
              aria-label={showPassword ? "Passwort verbergen" : "Passwort anzeigen"}>
              {showPassword ? "🙈" : "👁"}
            </button>
          </div>
        </div>
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Passwort wiederholen</label>
          <div className="relative">
            <input type={showConfirm ? "text" : "password"} value={confirm} onChange={e => setConfirm(e.target.value)}
              className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 pr-12 text-sprossa-ink text-base"
              placeholder="******" required />
            <button type="button" onClick={() => setShowConfirm(!showConfirm)}
              className="absolute inset-y-0 right-0 flex items-center px-3 text-lg cursor-pointer"
              aria-label={showConfirm ? "Passwort verbergen" : "Passwort anzeigen"}>
              {showConfirm ? "🙈" : "👁"}
            </button>
          </div>
        </div>

        <label className="flex items-start gap-3 rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sm text-sprossa-ink cursor-pointer">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            className="mt-1 size-4 shrink-0 accent-sprossa-green"
            required
          />
          <span>
            Ich akzeptiere die{" "}
            <a href="/agb" target="_blank" rel="noreferrer" className="font-semibold text-sprossa-green underline">AGB</a>{" "}
            und die{" "}
            <a href="/datenschutz" target="_blank" rel="noreferrer" className="font-semibold text-sprossa-green underline">Datenschutzerklärung</a>.
          </span>
        </label>

        {msg && (
          <div className="rounded-lg border border-sprossa-error/20 bg-sprossa-error/5 px-4 py-3 text-sm text-sprossa-error font-medium" role="alert">
            {msg}
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