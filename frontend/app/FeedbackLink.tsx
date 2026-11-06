"use client";

import { useEffect, useState } from "react";

/**
 * Zentraler Feedback-Zugang.
 *
 * Bewusst als mailto-Link und nicht als Formular: kein zusätzlicher
 * Endpunkt, keine Datenspeicherung, kein Spam-Schutz nötig — und der
 * Nutzer schreibt aus seinem gewohnten Mailprogramm. Der Kontext
 * (Bereich, Seite) wird in Betreff und Text vorbelegt, damit eine
 * Rückfrage ohne Nachfassen möglich ist.
 *
 * Die aktuelle Seite wird erst im Effekt gesetzt: `window` beim
 * Server-Rendern zu lesen würde einen Hydration-Mismatch erzeugen.
 */

const ADRESSE = "feedback@sprossa.de";

type Variante = "header" | "inline" | "floating";

export default function FeedbackLink({
  kontext,
  variante = "inline",
  detail,
}: {
  /** Kurzer Ort, z. B. "Dashboard" oder "Einkaufsliste" */
  kontext: string;
  variante?: Variante;
  /** Optionaler Zusatz (z. B. Plan-Monat), landet im Mailtext */
  detail?: string;
}) {
  const [seite, setSeite] = useState("");

  useEffect(() => {
    setSeite(window.location.pathname);
  }, []);

  const betreff = `[Sprossa] Feedback – ${kontext}`;
  const zeilen = ["Was ist dir aufgefallen?", "", "", "---", `Bereich: ${kontext}`];
  if (detail) zeilen.push(`Details: ${detail}`);
  if (seite) zeilen.push(`Seite: ${seite}`);
  zeilen.push("(Diese Zeilen helfen uns, die Stelle zu finden. Du kannst sie löschen.)");

  const href = `mailto:${ADRESSE}?subject=${encodeURIComponent(betreff)}&body=${encodeURIComponent(
    zeilen.join("\n"),
  )}`;

  const styles: Record<Variante, string> = {
    header:
      "rounded-lg px-3 py-2 text-sm font-bold text-sprossa-muted hover:bg-sprossa-sage hover:text-sprossa-green",
    inline:
      "rounded-xl border-2 border-sprossa-ink/10 bg-white px-4 py-3 text-sm font-bold text-sprossa-green hover:border-sprossa-green/40 hover:bg-sprossa-sage/40",
    floating:
      "fixed bottom-5 right-5 z-40 rounded-full bg-sprossa-green px-5 py-3 text-sm font-bold text-white shadow-[0_8px_24px_rgba(38,48,43,0.18)] hover:bg-sprossa-dark",
  };

  return (
    <a
      href={href}
      className={`inline-flex items-center gap-2 no-underline transition-colors ${styles[variante]}`}
      title={`Feedback per E-Mail an ${ADRESSE}`}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      Feedback
    </a>
  );
}
