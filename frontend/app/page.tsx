"use client";

import { useRef, useState } from "react";

/* ─── Icon-Sprache (statt Emoji) ─────────────────────────────────────────── */
function IconCalendar() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3A7D44" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="17" rx="3" />
      <path d="M3 9h18M8 2v4M16 2v4M8 14h3M8 17h6" />
    </svg>
  );
}

function IconFamily() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3A7D44" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="9" cy="8" r="3.2" />
      <path d="M2.5 20a6.5 6.5 0 0 1 13 0M17 5.5a3 3 0 0 1 0 5.8M18 20a6 6 0 0 0-3-5.2" />
    </svg>
  );
}

function IconBasket() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3A7D44" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 9h16l-1.4 10.2A2 2 0 0 1 16.6 21H7.4a2 2 0 0 1-2-1.8L4 9Z" />
      <path d="M8.5 9 12 3l3.5 6" />
    </svg>
  );
}

function IconCart({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#2C5F34" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="shrink-0">
      <circle cx="9" cy="21" r="1" />
      <circle cx="20" cy="21" r="1" />
      <path d="M1 1h4l2.7 13.4a2 2 0 0 0 2 1.6h9.7a2 2 0 0 0 2-1.6L23 6H6" />
    </svg>
  );
}

const WEEK = [
  ["Mo", "Linsen-Curry mit Kokos", "Cook once"],
  ["Di", "Curry-Reis-Bowl (Reste)", "Eat twice"],
  ["Mi", "Nudelauflauf mit Zucchini", "Schnell"],
  ["Do", "Salmon-Bowl mit Süßkartoffel", "Cook once"],
  ["Fr", "Bowl-Reste mit Ei", "Eat twice"],
  ["Sa", "Pizza-Pfanne, Familien-Favorit", "Genuss"],
  ["So", "Kürbissuppe mit Brot", "Sonntag"],
] as const;

export default function HomePage() {
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [statusOk, setStatusOk] = useState<boolean | null>(null);
  const [sending, setSending] = useState(false);
  const [emailError, setEmailError] = useState(false);
  const [consentError, setConsentError] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);

  function focusEmail() {
    emailRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    emailRef.current?.focus({ preventScroll: true });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatusMsg("");
    setStatusOk(null);
    setEmailError(false);
    setConsentError(false);

    const emailOk = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(email.trim());
    if (!emailOk) {
      setEmailError(true);
      setStatusMsg("Bitte prüft eure E-Mail-Adresse – dann sind wir startklar.");
      setStatusOk(false);
      emailRef.current?.focus();
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
      const params = new URLSearchParams(window.location.search);
      const utmSource = params.get("utm_source") || "organic";
      const utmCampaign = params.get("utm_campaign");
      const res = await fetch("/api/v1/waitlist/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          source: utmSource,
          utm_campaign: utmCampaign,
        }),
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
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-0 focus:top-0 focus:z-50 focus:rounded-br-xl focus:bg-sprossa-green focus:px-[18px] focus:py-3 focus:font-extrabold focus:text-white"
      >
        Zum Inhalt springen
      </a>

      <div className="mx-auto max-w-[1080px] px-6">
        <main id="main">
          {/* ═══ HERO ═══ */}
          <section className="grid grid-cols-1 items-center gap-9 pt-11 pb-16 lg:grid-cols-[1.05fr_.95fr] lg:gap-14">
            <div>
              <span className="mb-5 inline-block rounded-full bg-sprossa-sage px-3 py-1.5 text-xs font-extrabold uppercase tracking-[1.4px] text-sprossa-dark">
                Familien-Monatsplaner
              </span>

              <h1 className="mb-5 font-display text-[clamp(34px,5.2vw,56px)] font-semibold leading-[1.06] tracking-[-1px] text-balance text-sprossa-ink">
                Euer Monat wächst.
                <br />
                Wie{" "}
                <span className="text-sprossa-green">
                  ein Spross auf der Fensterbank.
                </span>
              </h1>

              <p className="mb-3 max-w-[34em] text-[18px] text-sprossa-muted-strong">
                Wochenende. Kühlschrank leer. „Was kochen wir?“ – dieselbe Frage in
                Millionen Küchen.
              </p>
              <p className="mb-7 max-w-[32em] text-[19px] font-semibold leading-[1.5] text-sprossa-ink">
                Sprossa pflanzt euren ganzen Monat: Rezepte für jeden Tag, die
                mitwachsen – passend zu eurem Kühlschrank, euren Kindern, eurem
                Budget.
              </p>

              {/* ═══ Waitlist-Formular (DSGVO-konform) ═══ */}
              <form
                id="early-access"
                onSubmit={handleSubmit}
                className="flex max-w-[480px] flex-col gap-3 sm:flex-row sm:items-end sm:gap-3"
                noValidate
              >
                <div className="flex flex-1 flex-col gap-1.5">
                  <label
                    htmlFor="early-email"
                    className="text-[12.5px] font-extrabold tracking-[.02em] text-sprossa-dark"
                  >
                    E-Mail für Early Access
                  </label>
                  <input
                    ref={emailRef}
                    id="early-email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setEmailError(false);
                    }}
                    placeholder="name@beispiel.de"
                    aria-label="E-Mail-Adresse"
                    aria-invalid={emailError || undefined}
                    aria-describedby="early-status"
                    autoComplete="email"
                    inputMode="email"
                    required
                    className={`w-full rounded-[14px] border-[1.5px] bg-white px-4 py-[15px] text-base text-sprossa-ink transition placeholder:text-[#8a938c] focus:outline-none focus:ring-4 ${
                      emailError
                        ? "border-sprossa-error focus:border-sprossa-error focus:ring-sprossa-error/15"
                        : "border-sprossa-ink/12 focus:border-sprossa-green focus:ring-sprossa-green/15"
                    }`}
                  />
                </div>

                <button
                  type="submit"
                  disabled={sending}
                  className="rounded-[14px] bg-sprossa-green px-[22px] py-[15px] text-base font-extrabold whitespace-nowrap text-white transition hover:bg-sprossa-dark active:translate-y-px disabled:cursor-progress disabled:bg-[#9db3a1] sm:w-auto w-full"
                >
                  {sending ? "Wird gesendet …" : "Early Access sichern"}
                </button>
              </form>

              {/* DSGVO: Einwilligung, NICHT vorbelegt */}
              <label
                className={`mt-3 flex max-w-[480px] items-start gap-3 text-[12.5px] leading-normal ${
                  consentError ? "text-sprossa-error" : "text-sprossa-muted-strong"
                }`}
              >
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => {
                    setConsent(e.target.checked);
                    setConsentError(false);
                  }}
                  className="mt-0.5 h-4 w-4 shrink-0"
                />
                <span>
                  Ich möchte per E-Mail über den Beta-Start von Sprossa informiert
                  werden und bin mit der Verarbeitung meiner E-Mail-Adresse zu diesem
                  Zweck gemäß der{" "}
                  <a
                    href="/datenschutz"
                    target="_blank"
                    rel="noopener"
                    className="font-semibold text-sprossa-green underline"
                  >
                    Datenschutzerklärung
                  </a>{" "}
                  einverstanden.
                </span>
              </label>

              {/* Status */}
              <p
                id="early-status"
                role={statusOk ? "status" : "alert"}
                aria-live={statusOk ? "polite" : "assertive"}
                className={`mt-2.5 min-h-[20px] text-[13px] leading-[1.5] ${
                  statusOk === true
                    ? "font-extrabold text-sprossa-dark"
                    : statusMsg
                      ? "font-bold text-sprossa-error"
                      : "text-sprossa-muted-strong"
                }`}
              >
                {statusMsg || "Kostenlos zum Launch · Früher Zugang · Kein Spam"}
              </p>
            </div>

            {/* ═══ Wochenplan-Beispiel ═══ */}
            <div
              className="overflow-hidden rounded-[22px] border border-sprossa-ink/12 bg-white shadow-[0_18px_40px_rgba(38,48,43,.08)]"
              aria-label="Beispiel: Wochenplan Woche 1"
            >
              <div className="flex items-center justify-between gap-2.5 border-b border-sprossa-ink/12 px-[22px] py-[18px]">
                <div className="text-[15px] font-extrabold text-sprossa-ink">
                  Wochenplan · Woche 1
                </div>
                <div className="rounded-full bg-sprossa-sage px-2.5 py-1 text-[11px] font-extrabold whitespace-nowrap text-sprossa-dark">
                  2 Kinder · Flexitarisch
                </div>
              </div>

              {WEEK.map(([tag, dish, chip]) => (
                <div
                  key={tag}
                  className="flex flex-wrap items-baseline gap-x-3 gap-y-1.5 border-b border-dashed border-sprossa-ink/12 px-[22px] py-[15px] last:border-b-0"
                >
                  <span className="w-[34px] shrink-0 text-xs font-extrabold uppercase tracking-[.08em] text-sprossa-dark">
                    {tag}
                  </span>
                  <span className="flex-1 text-[15px] font-bold text-sprossa-ink">
                    {dish}
                  </span>
                  <span className="text-[11.5px] font-extrabold whitespace-nowrap text-sprossa-terracotta-ink">
                    {chip}
                  </span>
                </div>
              ))}

              <div className="flex items-center gap-2 bg-sprossa-sage px-[22px] py-3.5 text-[13px] font-bold leading-[1.4] text-sprossa-dark">
                <IconCart />
                Einkaufsliste fertig – nach Kategorien sortiert
              </div>
            </div>
          </section>

          {/* ═══ Kern-Value ═══ */}
          <section className="grid grid-cols-1 gap-8 py-16 sm:grid-cols-3">
            {[
              {
                icon: <IconCalendar />,
                title: "Ein Monat, nicht eine Woche",
                desc: "Effiziente Monatspläne statt Kurzfrist-Denken. Cook-once-eat-twice spart Zeit und Geld.",
              },
              {
                icon: <IconFamily />,
                title: "Genau für eure Familie",
                desc: "Allergien, Vorlieben der Kinder, Zeit am Abend – jeder Tag passt zu euren Bedürfnissen.",
              },
              {
                icon: <IconBasket />,
                title: "Einkauf in einem Rutsch",
                desc: "Eine sortierte Einkaufsliste. Kein doppeltes Einkaufen, kein vergessenes Gemüse.",
              },
            ].map(({ icon, title, desc }) => (
              <div key={title}>
                <div className="mb-3.5 grid size-11 place-items-center rounded-xl bg-sprossa-sage">
                  {icon}
                </div>
                <h3 className="mb-1.5 font-display text-xl font-semibold text-sprossa-ink">
                  {title}
                </h3>
                <p className="text-[15px] text-sprossa-muted-strong">{desc}</p>
              </div>
            ))}
          </section>
        </main>
      </div>

      {/* ═══ So einfach ═══ */}
      <section className="border-y border-sprossa-ink/12 bg-white py-16">
        <div className="mx-auto max-w-[1080px] px-6">
          <div className="mb-2.5 text-center">
            <div className="text-xs font-extrabold uppercase tracking-[1.4px] text-sprossa-dark">
              So einfach
            </div>
            <h2 className="mx-auto mt-2.5 mb-7 font-display text-[clamp(26px,3.4vw,34px)] font-semibold leading-[1.15] text-balance text-sprossa-ink">
              Drei Schritte zu mehr Ruhe in der Küche
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-[26px] sm:grid-cols-3 sm:gap-10">
            {[
              {
                num: "1",
                title: "Euer Profil",
                desc: "Wer kocht mit? Allergien? Wie viel Zeit am Abend? Einmal ausfüllen.",
              },
              {
                num: "2",
                title: "Monat wird geplant",
                desc: "Rezepte, Zubereitung, Kinder-Tipps und saisonale Zutaten – automatisch.",
              },
              {
                num: "3",
                title: "Einkaufsliste fertig",
                desc: "Nach Kategorien sortiert, für einen entspannten Einkaufsgang.",
              },
            ].map(({ num, title, desc }, i, arr) => (
              <div key={num} className="relative pt-1.5">
                <div className="mb-1.5 font-display text-[40px] leading-none text-sprossa-green/45">
                  {num}
                </div>
                <h3 className="mb-1.5 text-[17px] font-extrabold text-sprossa-ink">
                  {title}
                </h3>
                <p className="text-[14.5px] text-sprossa-muted-strong">{desc}</p>
                {i < arr.length - 1 && (
                  <div
                    aria-hidden="true"
                    className="absolute right-[-16px] top-[26px] hidden h-px w-[calc(100%-48px)] bg-[repeating-linear-gradient(90deg,rgba(38,48,43,.12)_0_6px,transparent_6px_12px)] sm:block"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <div className="mx-auto max-w-[1080px] px-6">
        <section className="py-16 text-center">
          <div className="rounded-[22px] bg-sprossa-sage px-5 py-11">
            <h2 className="mx-auto mb-3 max-w-[18em] font-display text-[clamp(26px,3.6vw,36px)] font-semibold leading-[1.15] text-balance text-sprossa-ink">
              Schluss mit der „Was-kochen-wir“-Frage.
            </h2>
            <p className="mx-auto mb-6 max-w-[36em] text-sprossa-muted-strong">
              Seid unter den Ersten – sichert euch Early Access und spart euch ab dem
              Launch jede Woche die Planung.
            </p>
            <button
              type="button"
              onClick={focusEmail}
              className="rounded-[14px] bg-sprossa-green px-8 py-4 text-[17px] font-extrabold text-white transition hover:bg-sprossa-dark active:translate-y-px"
            >
              Early Access sichern
            </button>
            <p className="mt-3 text-[12.5px] text-sprossa-muted-strong">
              Kostenlos zum Launch · Kein Spam · Jederzeit abbestellbar
            </p>
          </div>

          {/* ═══ Footer ═══ */}
          <footer className="mt-0 flex flex-col justify-between gap-3 border-t border-sprossa-ink/12 pt-6 pb-9 text-[13px] text-sprossa-muted-strong sm:flex-row sm:flex-wrap">
            <span>Sprossa · euer Monat, klug geplant</span>
            <nav className="flex flex-wrap gap-[18px]" aria-label="Rechtliches">
              <a href="/impressum" className="font-bold text-sprossa-dark no-underline hover:underline">
                Impressum
              </a>
              <a href="/datenschutz" className="font-bold text-sprossa-dark no-underline hover:underline">
                Datenschutz
              </a>
              <a href="/agb" className="font-bold text-sprossa-dark no-underline hover:underline">
                AGB
              </a>
              <a href="/bildnachweis" className="font-bold text-sprossa-dark no-underline hover:underline">
                Bildnachweis
              </a>
            </nav>
          </footer>
        </section>
      </div>
    </>
  );
}
