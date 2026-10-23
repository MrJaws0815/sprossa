"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  function getToken(): string | null {
    const params = new URLSearchParams(window.location.search);
    return params.get("token");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");

    const token = getToken();
    if (!token) { setMsg("❌ Fehlender oder ungültiger Token."); return; }
    if (confirm !== password) { setMsg("❌ Passwörter stimmen nicht überein"); return; }
    if (password.length < 8) { setMsg("❌ Mindestens 8 Zeichen"); return; }

    setLoading(true);
    try {
      const r = await fetch(`${API}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setMsg("❌ " + ((d as any).detail || "Token ungültig oder abgelaufen."));
        return;
      }
      window.location.href = "/login";
    } catch (e: any) {
      setMsg("❌ " + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md mt-16 px-4">
      <h1 className="font-display text-3xl font-bold text-sprossa-ink mb-1">Neues Passwort</h1>
      <p className="mb-8 text-sprossa-muted">Setze ein neues Passwort für dein Konto.</p>

      <form onSubmit={handleSubmit} className="space-y-4 w-full">
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Neues Passwort</label>
          <input type="password" value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full rounded-xl border-2 border-sprossa-muted/20 bg-white px-4 py-3 text-sprossa-ink text-base"
            placeholder="Mindestens 8 Zeichen" required minLength={8} />
        </div>
        <div>
          <label className="block mb-1 text-sm font-semibold text-sprossa-ink">Passwort wiederholen</label>
          <input type="password" value={confirm}
            onChange={e => setConfirm(e.target.value)}
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
          {loading ? "Einen Moment …" : "Passwort zurücksetzen"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center text-sprossa-muted">
        Zurück zum <a href="/login" className="font-semibold text-sprossa-green underline">Login</a>
      </p>
    </div>
  );
}