import Link from "next/link";

export default function DatenschutzPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Datenschutzerklärung</h1>

      <h2 className="text-xl font-bold mt-6 mb-3">1. Verantwortlicher</h2>
      <p>Verantwortlich für die Datenverarbeitung auf dieser Website ist:</p>
      <address className="not-italic mt-2">
        The Oaktree<br />
        Ickerner Heide 4a<br />
        45731 Waltrop<br />
        Deutschland<br />
        E-Mail: hallo@sprossa.de
      </address>

      <h2 className="text-xl font-bold mt-6 mb-3">2. Allgemeines</h2>
      <p>Wir nehmen den Schutz Ihrer persönlichen Daten ernst. Diese Datenschutzerklärung informiert Sie darüber, wie wir Ihre personenbezogenen Daten im Zusammenhang mit der Nutzung dieser Website und der Anmeldung zur Beta-/Warteliste verarbeiten.</p>

      <h2 className="text-xl font-bold mt-6 mb-3">3. Erhebung und Verarbeitung (Warteliste)</h2>
      <p>Wenn Sie sich für die Beta-Phase vormerken lassen, verarbeiten wir folgende Daten:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>E-Mail-Adresse</li>
        <li>Datum und Uhrzeit der Anmeldung</li>
        <li>Ggfs. technische Logdaten (IP-Adresse, User-Agent) zur Sicherstellung der Funktion</li>
      </ul>

      <h2 className="text-xl font-bold mt-6 mb-3">4. Zweck der Verarbeitung</h2>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>Versand von Informationen zum Early-Access/Beta-Start von Sprossa</li>
        <li>Kommunikation zu Ihrer Anmeldung</li>
        <li>Sicherstellung und Verbesserung des Anmeldevorgangs</li>
      </ul>

      <h2 className="text-xl font-bold mt-6 mb-3">5. Rechtsgrundlagen</h2>
      <p>Die Verarbeitung Ihrer E-Mail-Adresse erfolgt auf Grundlage Ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO), die Sie im Rahmen der Double-Opt-in-Anmeldung erteilen. Technisch notwendige Logdaten stützen sich auf unser berechtigtes Interesse an der Sicherheit und Funktionsfähigkeit der Website (Art. 6 Abs. 1 lit. f DSGVO).</p>

      <h2 className="text-xl font-bold mt-6 mb-3">6. Speicherdauer</h2>
      <p>Ihre E-Mail-Adresse speichern wir nur so lange, wie es für den Zweck (Beta-Benachrichtigung) erforderlich ist. Sie können Ihre Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen. Nach Widerruf oder Zweckwegfall löschen wir Ihre Daten unverzüglich. Ohne Widerruf löschen wir die Daten spätestens 12 Monate nach dem Beta-Start.</p>

      <h2 className="text-xl font-bold mt-6 mb-3">7. Ihre Rechte (Art. 15–21 DSGVO)</h2>
      <p>Sie haben das Recht auf:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Auskunft</strong> über die gespeicherten Daten (Art. 15)</li>
        <li><strong>Berichtigung</strong> unrichtiger Daten (Art. 16)</li>
        <li><strong>Löschung</strong> (Art. 17, "Recht auf Vergessenwerden")</li>
        <li><strong>Einschränkung der Verarbeitung</strong> (Art. 18)</li>
        <li><strong>Datenübertragbarkeit</strong> (Art. 20)</li>
        <li><strong>Widerspruch</strong> gegen die Verarbeitung (Art. 21)</li>
        <li><strong>Widerruf der Einwilligung</strong> mit Wirkung für die Zukunft (Art. 7 Abs. 3)</li>
      </ul>
      <p className="mt-2">Zur Ausübung Ihrer Rechte genügt eine E-Mail an <strong>hallo@sprossa.de</strong>.</p>

      <h2 className="text-xl font-bold mt-6 mb-3">8. Hosting</h2>
      <p>Diese Website wird bei einem Dienstleister in der Europäischen Union gehostet: Hetzner Online GmbH, Industriestr. 25, 91710 Gunzenhausen (Rechenzentrum in Falkenstein, Deutschland). Mit dem Hosting-Anbieter besteht ein Auftragsverarbeitungsvertrag (AVV) gemäß Art. 28 DSGVO.</p>

      <h2 className="text-xl font-bold mt-6 mb-3">9. SSL/TLS-Verschlüsselung</h2>
      <p>Diese Website nutzt aus Sicherheitsgründen eine SSL-/TLS-Verschlüsselung (HTTPS).</p>

      <h2 className="text-xl font-bold mt-6 mb-3">10. Keine Weitergabe an Dritte</h2>
      <p>Ohne Ihre ausdrückliche Einwilligung geben wir Ihre personenbezogenen Daten nicht an Dritte weiter.</p>

      <hr className="mt-10 border-sprossa-muted/20" />
      <p className="text-sm text-sprossa-muted">Stand: Oktober 2026</p>
      <div className="mt-6">
        <Link href="/" className="text-sprossa-green">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}