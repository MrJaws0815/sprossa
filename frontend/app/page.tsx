"use client";

import { useState } from "react";

export default function HomePage() {
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [statusOk, setStatusOk] = useState<boolean | null>(null);
  const [sending, setSending] = useState(false);
  const [emailError, setEmailError] = useState(false);
  const [consentError, setConsentError] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatusMsg("");
    setStatusOk(null);
    setEmailError(false);
    setConsentError(false);

    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
    if (!emailOk) {
      setEmailError(true);
      setStatusMsg("Bitte gib eine gültige E-Mail-Adresse ein.");
      setStatusOk(false);
      return;
    }
    if (!consent) {
      setConsentError(true);
      setStatusMsg("Bitte stimme der Verarbeitung deiner E-Mail-Adresse zu.");
      setStatusOk(false);
      return;
    }

    setSending(true);
    try {
      const res = await fetch("/api/v1/waitlist/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const json = await res.json();
      setStatusMsg(json.message || "✅ Danke – du bist auf der Liste!");
      setStatusOk(true);
      setEmail("");
      setConsent(false);
    } catch {
      setStatusMsg("Ups, das hat nicht geklappt. Probier es gleich nochmal.");
      setStatusOk(false);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6">
      {/* ═══ HERO (Header kommt global aus app/Header.tsx via layout) ═══ */}
      <section className="grid grid-cols-2 gap-10 items-start pt-14 pb-12">
        <div>
          <span className="inline-block text-xs font-bold tracking-widest uppercase text-sprossa-green bg-sprossa-sage px-3 py-2 rounded-full mb-5">
            Familien-Monatsplaner
          </span>
          <h1 className="font-display text-6xl font-semibold leading-tight tracking-tight mb-5 text-sprossa-ink">
            Euer Monat wächst.
            <br />
            <span className="text-sprossa-green">Wie ein Spross auf der Fensterbank.</span>
          </h1>
          <p className="text-lg text-sprossa-muted mb-3.5">
            Wochenende. Kühlschrank leer. "Was kochen wir?" – Musik in #millionen Küchen.
          </p>
          <p className="text-xl font-semibold mb-7 text-sprossa-ink">
            Sprossa pflanzt euren ganzen Monat: Rezepte für jeden Tag, die mitwächst – passend zu eurem Kühlschrank, euren Kindern, eurem Budget.
          </p>

          {/* ═══ Waitlist-Formular (DSGVO-konform) – id "early-access" als Sprungziel ═══ */}
          <form id="early-access" onSubmit={handleSubmit} className="flex flex-col gap-3 max-w-lg" noValidate>
            <div className="flex gap-3">
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setEmailError(false); }}
                placeholder="E-Mail für Early Access"
                aria-label="E-Mail-Adresse"
                autoComplete="email"
                required
                className={`flex-1 px-5 py-4 border-2 rounded-xl text-base bg-white ${emailError ? "border-sprossa-error" : "border-sprossa-muted/20"} text-sprossa-ink`}
              />
              <button
                type="submit"
                disabled={sending}
                className="px-6 py-4 rounded-xl bg-sprossa-green text-white text-base font-bold whitespace-nowrap disabled:opacity-60"
              >
                {sending ? "Wird gesendet…" : "Early Access sichern"}
              </button>
            </div>
            {/* DSGVO: Einwilligung, NICHT vorbelegt */}
            <label className={`touch-target flex gap-3 items-start text-xs leading-normal ${consentError ? "text-sprossa-error" : "text-sprossa-muted"}`}>
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => { setConsent(e.target.checked); setConsentError(false); }}
                className="mt-1 w-4 h-4 shrink-0"
              />
              <span>
                Ich möchte per E-Mail über den Beta-Start von Sprossa informiert werden und bin mit der Verarbeitung meiner E-Mail-Adresse zu diesem Zweck gemäß der{" "}
                <a href="/datenschutz" target="_blank" rel="noopener" className="underline text-sprossa-green">Datenschutzerklärung</a> einverstanden.
              </span>
            </label>
            {/* Status */}
            {statusMsg && (
              <div role="status" aria-live="polite" className={`text-sm font-bold ${statusOk ? "text-sprossa-dark" : "text-sprossa-error"}`}>
                {statusMsg}
              </div>
            )}
          </form>
          <p className="text-xs text-sprossa-muted mt-3">
            🚀 Kostenlos zum Launch · Früher Zugang · Kein Spam
          </p>
        </div>

        {/* ═══ Wochenplan-Beispiel-Karte ═══ */}
        <div className="rounded-2xl border border-sprossa-ink/10 bg-white shadow-xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-5 border-b border-sprossa-ink/10">
            <div className="font-bold">Wochenplan · Woche 1</div>
            <div className="text-xs font-bold text-sprossa-dark bg-sprossa-sage px-3 py-1 rounded-full">
              2 Kids · Flexitarisch
            </div>
          </div>
          {[
            ["Mo", "Linsen-Curry mit Kokos", "⟲ Cook once"],
            ["Di", "Curry-Reis-Bowl (Rest)", "eat twice"],
            ["Mi", "Nudelauflauf mit Zucchini", "Schnell"],
            ["Do", "Salmon-Bowl mit Süßkartoffel", "⟲ Cook once"],
            ["Fr", "Bowl-Reste mit Ei", "eat twice"],
            ["Sa", "Pizza-Pfanne, Familien-Favorit", "Genuss"],
            ["So", "Kürbissuppe mit Brot", "Sonntag"],
          ].map(([tag, dish, chip]) => (
            <div key={tag} className="flex items-center justify-between px-6 py-3 border-b border-dashed border-sprossa-ink/10">
              <span className="font-bold uppercase text-sprossa-green text-xs tracking-wider w-15">{tag}</span>
              <span className="font-bold text-sprossa-ink">{dish}</span>
              <span className="text-xs font-bold text-sprossa-terracotta">{chip}</span>
            </div>
          ))}
          <div className="flex items-center gap-2 px-6 py-3 bg-sprossa-sage text-sm font-bold text-sprossa-dark">
            🛒 Einkaufsliste fertig generiert – nach Kategorien sortiert
          </div>
        </div>
      </section>

      {/* ═══ Kern-Value ═══ */}
      <section className="grid grid-cols-3 gap-7 pt-14 pb-20">
        {[
          { ico: "🗓️", title: "Ein Monat, nicht eine Woche", desc: "Effiziente Monatspläne statt Kurzfrist-Denken. Cook-Once-Eat-Twice spart Zeit und Geld." },
          { ico: "🧒", title: "Genau für eure Familie", desc: "Allergien, Kindern-Vorlieben, Zeitbudget – jeder Tag passt zu euren Bedürfnissen." },
          { ico: "🧺", title: "Einkauf in einem Rutsch", desc: "Eine sortierte Einkaufsliste. Kein doppelt Einkaufen, kein vergessenes Gemüse." },
        ].map(({ ico, title, desc }) => (
          <div key={title}>
            <div className="text-3xl mb-3 text-sprossa-terracotta">{ico}</div>
            <h3 className="font-display text-xl mb-2 text-sprossa-green">{title}</h3>
            <p className="text-sm text-sprossa-muted">{desc}</p>
          </div>
        ))}
      </section>

      {/* ═══ How It Works ═══ */}
      <section className="bg-white pt-24 pb-24 border-t border-b border-sprossa-ink/10">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-2.5 text-center">
            <div className="text-xs font-bold tracking-widest uppercase text-sprossa-green">So einfach</div>
            <h2 className="font-display text-4xl text-center mb-10 mt-5 text-sprossa-green">Drei Schritte zu mehr Ruhe in der Küche</h2>
          </div>
          <div className="grid grid-cols-3 gap-10">
            {[
              { num: "1", title: "Euer Profil", desc: "Wer kocht mit? Allergien? Wie viel Zeit am Abend? Einmal ausfüllen." },
              { num: "2", title: "Monat wird geplant", desc: "Rezepte, Zubereitung, Kinder-Tipps und saisonale Zutaten – automatisch." },
              { num: "3", title: "Einkaufsliste fertig", desc: "Nach Kategorien sortiert, für einen effizienten Einkaufsgang im Supermarkt." },
            ].map(({ num, title, desc }) => (
              <div key={num}>
                <div className="font-display text-5xl text-sprossa-green opacity-40 leading-none mb-2">{num}</div>
                <h3 className="text-lg mb-1.5 text-sprossa-green">{title}</h3>
                <p className="text-sm text-sprossa-muted">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section id="cta" className="text-center pt-24 pb-28 bg-sprossa-sage">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-4xl max-w-xl mx-auto mb-4">
            Schluss mit der „Was-kochen-wir-Frage".
          </h2>
          <p className="text-sprossa-muted mb-7">
            Sei unter den Ersten – sicher dir Early Access und spare dir ab dem Launch die Woche.
          </p>
        </div>
      </section>

      {/* ═══ Footer (Impressum + Datenschutz, DSGVO-Pflicht) ═══ */}
      <footer className="border-t border-sprossa-ink/10 pt-10 pb-12">
        <div className="flex justify-between flex-wrap gap-3 text-sm text-sprossa-muted">
          <span>🌱 Sprossa · euer Monat, klug geplant</span>
          <div className="flex gap-5 flex-wrap">
            <a href="/datenschutz" className="text-sprossa-green font-semibold no-underline">Datenschutz</a>
            <a href="/impressum" className="text-sprossa-green font-semibold no-underline">Impressum</a>
            <a href="/agb" className="text-sprossa-green font-semibold no-underline">AGB</a>
          </div>
        </div>
        <div className="mt-3 text-xs text-sprossa-muted opacity-80">
          © Sprossa. Alle Rechte vorbehalten.
        </div>
      </footer>
    </div>
  );
}