"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import SprossMark from "./SprossMark";

/**
 * Sprossa – Globaler Header (erscheint auf allen Seiten via Layout).
 * Marke "Sprossa" als Link zurück zur Startseite (/).
 *
 * Kontextabhängiger rechter Link:
 *  - im App-Bereich (/dashboard, /onboarding …) → "Zum Dashboard" bzw. "Zum Plan"
 *  - auf der Landingpage → "Early Access" (springt zur Mail-Eingabe, id "early-access")
 * Vorher führte "Early Access" auch eingeloggte Nutzer zurück auf die Marketing-Seite.
 */
export default function SprossaHeader() {
  const pathname = usePathname() ?? "/";
  const inApp = pathname.startsWith("/dashboard") || pathname.startsWith("/onboarding");

  return (
    <header className="border-b border-sprossa-ink/10 bg-sprossa-cream">
      <div className="mx-auto max-w-[1080px] px-6">
        <nav className="flex items-center justify-between py-[18px]">
          {/* Marke → zurück zur Startseite */}
          <Link
            href="/"
            className="flex items-center gap-[10px] font-bold text-xl tracking-tight text-sprossa-ink no-underline"
          >
            <span className="grid size-[34px] place-items-center rounded-[10px] bg-sprossa-green">
              <SprossMark size={20} />
            </span>
            Sprossa
            <span className="ml-[6px] text-sm font-normal text-sprossa-muted">
              · euer Monat, klug geplant
            </span>
          </Link>

          {inApp ? (
            <Link
              href="/dashboard"
              className="font-bold text-sm text-sprossa-green no-underline"
            >
              Zum Dashboard
            </Link>
          ) : (
            <Link
              href="/#early-access"
              className="font-bold text-sm text-sprossa-green no-underline"
            >
              Early Access
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
