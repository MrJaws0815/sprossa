import Link from "next/link";

export default function DatenschutzPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Datenschutzerklärung</h1>

      <h2 className="text-xl font-bold mt-6 mb-3">1. Verantwortlicher</h2>
      <p>Verantwortlich für die Datenverarbeitung ist:</p>
      <address className="not-italic mt-2">
        The Oaktree<br />
        Ickerner Heide 4a<br />
        45731 Waltrop<br />
        Deutschland<br />
        E-Mail: hallo@sprossa.de
      </address>

      <h2 className="text-xl font-bold mt-6 mb-3">2. Allgemeines</h2>
      <p>
        Wir nehmen den Schutz Ihrer persönlichen Daten ernst. Diese Erklärung
        informiert Sie darüber, welche Daten wir bei der Nutzung der Website, bei der
        Anmeldung zur Warteliste und bei der Nutzung der Sprossa-Anwendung verarbeiten.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">3. Warteliste (Beta-Anmeldung)</h2>
      <p>Wenn Sie sich für die Beta-Phase vormerken lassen, verarbeiten wir:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>E-Mail-Adresse</li>
        <li>Datum und Uhrzeit der Anmeldung sowie den Bestätigungsstatus</li>
        <li>optional: Name und Haushaltsgröße</li>
        <li>Herkunft der Anmeldung (UTM-Parameter, z.&nbsp;B. Pinterest oder Instagram)</li>
        <li>technische Logdaten (IP-Adresse, User-Agent) zur Sicherstellung der Funktion</li>
      </ul>
      <p className="mt-2">
        Die Anmeldung erfolgt im Double-Opt-in-Verfahren: Erst nach Klick auf den
        Bestätigungslink in unserer E-Mail gilt sie als abgeschlossen.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">4. Konto und Nutzung der Anwendung</h2>
      <p>Bei der Registrierung und Nutzung von Sprossa verarbeiten wir:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Kontodaten:</strong> E-Mail-Adresse, Passwort (ausschließlich als Hash gespeichert, nie im Klartext), Anzeigename</li>
        <li><strong>Haushaltsdaten:</strong> Haushaltsname, Anzahl und Alter der Mitglieder, optional Gewichtsangaben zur Portionsberechnung</li>
        <li><strong>Ernährungsprofil:</strong> Ernährungsform, Fokusthemen, Abneigungen</li>
        <li><strong>Gesundheitsbezogene Angaben:</strong> Allergien und Unverträglichkeiten, die Sie für Haushaltsmitglieder eintragen</li>
        <li><strong>Nutzungsdaten:</strong> erzeugte Monatspläne, Rezeptauswahl, Einkaufslisten, abgehakte Einkaufspositionen</li>
      </ul>
      <p className="mt-2">
        Zweck ist die Erstellung und Verwaltung Ihrer Ernährungspläne, Rezeptvorschläge
        und Einkaufslisten.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">5. Besondere Kategorien personenbezogener Daten (Art. 9 DSGVO)</h2>
      <p>
        Allergien und Unverträglichkeiten sind Gesundheitsdaten im Sinne von Art. 9
        Abs. 1 DSGVO. Wir verarbeiten sie ausschließlich, um Rezepte und Pläne
        entsprechend Ihren Angaben zu filtern.
      </p>
      <p className="mt-2">
        Rechtsgrundlage ist Ihre ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a
        DSGVO, die Sie beim Eintragen der Angaben erteilen. Sie können sie jederzeit
        widerrufen; wir löschen die Angaben dann und filtern nicht mehr danach. Die
        Rechtmäßigkeit der bis zum Widerruf erfolgten Verarbeitung bleibt unberührt.
      </p>
      <p className="mt-2">
        <strong>Wichtig:</strong> Die Angaben beruhen auf Ihrer Selbstauskunft. Sprossa
        ersetzt keine medizinische Beratung und keine Prüfung der Zutaten auf
        Kreuzkontaminationen.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">6. Reichweitenmessung</h2>
      <p>Beim Aufruf der Website erfassen wir:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>aufgerufenen Pfad und Referrer</li>
        <li>UTM-Parameter (Kampagnenherkunft)</li>
        <li>Geräteklasse (mobil/Desktop)</li>
        <li>einen täglich wechselnden Pseudonym-Hash aus IP-Adresse, User-Agent und Datum</li>
      </ul>
      <p className="mt-2">
        Wir setzen dafür <strong>keine Cookies</strong>, speichern keine IP-Adressen im
        Klartext und geben die Daten nicht an Dritte weiter. Zweck ist die Messung,
        welche Kanäle tatsächlich Besucher bringen. Rechtsgrundlage ist unser
        berechtigtes Interesse an einer datensparsamen Reichweitenmessung
        (Art. 6 Abs. 1 lit. f DSGVO). Die Daten werden nach 90 Tagen gelöscht.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">7. Lokale Speicherung und Cookies</h2>
      <p>
        Wir nutzen <code>localStorage</code> und <code>sessionStorage</code>, um den
        Zustand der Oberfläche zu halten — etwa abgehakte Einkaufspositionen und die
        Information, ob eine Seitenansicht in dieser Sitzung bereits gezählt wurde.
        Diese Speicherung ist für die Funktion erforderlich und enthält keine Werbe-
        oder Tracking-IDs.
      </p>
      <p className="mt-2">
        Nach der Anmeldung setzen wir ein technisch notwendiges Cookie
        (<code>sprossa_token</code>, httpOnly, SameSite=Lax), das Ihre Sitzung hält.
        Es enthält keine Werbeinformationen und wird beim Abmelden gelöscht.
      </p>
      <p className="mt-2">
        Rechtsgrundlage für beides ist § 25 Abs. 2 Nr. 2 TDDDG (unbedingt erforderlich)
        sowie Art. 6 Abs. 1 lit. b DSGVO für die Anmeldung.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">8. Rechtsgrundlagen</h2>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>Warteliste: Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO)</li>
        <li>Konto und Anwendung: Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)</li>
        <li>Gesundheitsdaten: ausdrückliche Einwilligung (Art. 9 Abs. 2 lit. a DSGVO)</li>
        <li>Reichweitenmessung: berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO)</li>
        <li>technisch notwendige Logdaten: berechtigtes Interesse an Sicherheit und Funktionsfähigkeit (Art. 6 Abs. 1 lit. f DSGVO)</li>
      </ul>

      <h2 className="text-xl font-bold mt-6 mb-3">9. Speicherdauer</h2>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Warteliste:</strong> bis zum Widerruf, spätestens 12 Monate nach dem Beta-Start</li>
        <li><strong>Kontodaten:</strong> bis zur Löschung des Kontos, danach Löschung innerhalb von 30 Tagen (einschließlich Sicherungskopien)</li>
        <li><strong>Pläne, Rezepte, Einkaufslisten:</strong> bis zur Kontolöschung</li>
        <li><strong>Reichweitenmessung:</strong> 90 Tage</li>
      </ul>
      <p className="mt-2">
        Sie können Ihre Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen.
        Nach Widerruf oder Zweckwegfall löschen wir Ihre Daten unverzüglich.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">10. Empfänger und Auftragsverarbeiter</h2>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Hetzner Online GmbH</strong>, Gunzenhausen — Hosting von Server und Datenbank, Auftragsverarbeitungsvertrag nach Art. 28 DSGVO</li>
        <li><strong>E-Mail-Versand</strong> — für Bestätigungs- und Benachrichtigungsmails, Auftragsverarbeitungsvertrag nach Art. 28 DSGVO</li>
      </ul>
      <p className="mt-2">Eine Weitergabe zu Werbezwecken findet nicht statt.</p>

      <h2 className="text-xl font-bold mt-6 mb-3">11. Ihre Rechte (Art. 15–21 DSGVO)</h2>
      <p>Sie haben das Recht auf:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Auskunft</strong> über die gespeicherten Daten (Art. 15)</li>
        <li><strong>Berichtigung</strong> unrichtiger Daten (Art. 16)</li>
        <li><strong>Löschung</strong> (Art. 17, „Recht auf Vergessenwerden“)</li>
        <li><strong>Einschränkung der Verarbeitung</strong> (Art. 18)</li>
        <li><strong>Datenübertragbarkeit</strong> (Art. 20)</li>
        <li><strong>Widerspruch</strong> gegen die Verarbeitung (Art. 21)</li>
        <li><strong>Widerruf der Einwilligung</strong> mit Wirkung für die Zukunft (Art. 7 Abs. 3)</li>
      </ul>
      <p className="mt-2">Zur Ausübung Ihrer Rechte genügt eine E-Mail an <strong>hallo@sprossa.de</strong>.</p>

      <h2 className="text-xl font-bold mt-6 mb-3">12. Beschwerderecht</h2>
      <p>
        Sie können sich bei einer Datenschutz-Aufsichtsbehörde beschweren, insbesondere
        bei der für Ihren Wohnsitz zuständigen Behörde. Für uns zuständig ist die
        Landesbeauftragte für Datenschutz und Informationsfreiheit Nordrhein-Westfalen.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">13. SSL/TLS-Verschlüsselung</h2>
      <p>
        Diese Website nutzt aus Sicherheitsgründen eine SSL-/TLS-Verschlüsselung (HTTPS).
      </p>

      <hr className="mt-10 border-sprossa-ink/12" />
      <p className="text-sm text-sprossa-muted-strong">Stand: November 2026</p>
      <div className="mt-6">
        <Link href="/" className="font-semibold text-sprossa-green underline">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}
