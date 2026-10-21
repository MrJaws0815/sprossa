import Link from "next/link";

export default function ImpressumPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Impressum</h1>

      <h2 className="text-xl font-bold mt-6 mb-3">Angaben gemäß § 5 DDG und § 18 Abs. 2 MStV</h2>

      <p><strong>The Oaktree</strong></p>
      <address className="not-italic mt-1">
        Ickerner Heide 4a<br />
        45731 Waltrop<br />
        Deutschland
      </address>

      <h2 className="text-xl font-bold mt-6 mb-3">Vertreten durch</h2>
      <p>Sebastian Westhoff</p>

      <h2 className="text-xl font-bold mt-6 mb-3">Kontakt</h2>
      <p>E-Mail: <a href="mailto:hallo@sprossa.de" className="text-sprossa-green">hallo@sprossa.de</a></p>

      <h2 className="text-xl font-bold mt-6 mb-3">Umsatzsteuer-ID</h2>
      <p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: DE335535698</p>

      <h2 className="text-xl font-bold mt-6 mb-3">EU-Streitschlichtung</h2>
      <p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: <a href="https://ec.europa.eu/consumers/odr/" className="text-sprossa-green">https://ec.europa.eu/consumers/odr/</a>. Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>

      <hr className="mt-10 border-sprossa-muted/20" />

      <div className="mt-6">
        <Link href="/" className="text-sprossa-green">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}