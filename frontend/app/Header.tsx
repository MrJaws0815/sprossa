import Link from "next/link";

/**
 * Sprossa – Globaler Header (erscheint auf allen Seiten via Layout).
 * Marke "🌱 Sprossa" als Link zurück zur Startseite (/).
 */
export default function SprossaHeader() {
  return (
    <header className="border-b border-sprossa-ink/10 bg-sprossa-cream">
      <div className="mx-auto max-w-[1080px] px-6">
        <nav className="flex items-center justify-between py-[18px]">
          {/* Marke → zurück zur Startseite */}
          <Link
            href="/"
            className="flex items-center gap-[10px] font-bold text-xl tracking-tight text-sprossa-ink no-underline"
          >
            <span className="grid size-[34px] place-items-center rounded-[10px] bg-sprossa-green text-white text-lg">
              🌱
            </span>
            Sprossa
            <span className="ml-[6px] text-sm font-normal text-sprossa-muted">
              · euer Monat, klug geplant
            </span>
          </Link>

          {/* Early-Access → springt zur Mail-Eingabe (Formular id "early-access") */}
          <Link
            href="/#early-access"
            className="font-bold text-sm text-sprossa-green no-underline"
          >
            Early Access
          </Link>
        </nav>
      </div>
    </header>
  );
}