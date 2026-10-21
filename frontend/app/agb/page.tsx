import Link from "next/link";

export default function AgbPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Allgemeine Geschäftsbedingungen (AGB)</h1>
      <p className="text-sprossa-muted mb-4">
        Die AGB für den späteren Produktivbetrieb von Sprossa werden hier veröffentlicht, 
        sobald der Dienst in die kostenpflichtige Phase startet.
      </p>
      <p className="text-sprossa-muted mb-4">
        Während der aktuellen Beta-Phase (kostenlose Testphase) gelten die 
        <Link href="/datenschutz" className="text-sprossa-green">Datenschutzerklärung</Link> 
        und das <Link href="/impressum" className="text-sprossa-green">Impressum</Link>.
      </p>
      <p className="text-sprossa-muted">
        Für Fragen: <a href="mailto:hallo@sprossa.de" className="text-sprossa-green">hallo@sprossa.de</a>
      </p>

      <hr className="mt-10 border-sprossa-muted/20" />

      <div className="mt-6">
        <Link href="/" className="text-sprossa-green">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}