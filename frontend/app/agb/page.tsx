import Link from "next/link";

export default function AgbPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Allgemeine Geschäftsbedingungen (AGB)</h1>
      <p className="text-sprossa-muted-strong mb-4">
        Die AGB für den späteren Produktivbetrieb von Sprossa werden hier veröffentlicht, 
        sobald der Dienst in die kostenpflichtige Phase startet.
      </p>
      <p className="text-sprossa-muted-strong mb-4">
        Während der aktuellen Beta-Phase (kostenlose Testphase) gelten die{" "}
        <Link href="/datenschutz" className="font-semibold text-sprossa-green underline">Datenschutzerklärung</Link>{" "}
        und das <Link href="/impressum" className="font-semibold text-sprossa-green underline">Impressum</Link>.
      </p>
      <p className="text-sprossa-muted-strong">
        Für Fragen: <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">hallo@sprossa.de</a>
      </p>

      <hr className="mt-10 border-sprossa-ink/12" />

      <div className="mt-6">
        <Link href="/" className="font-semibold text-sprossa-green underline">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}