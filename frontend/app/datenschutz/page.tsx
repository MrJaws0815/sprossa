import Link from "next/link";

export default function DatenschutzPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Datenschutzerklärung</h1>

      <p className="text-sprossa-muted-strong mb-2">
        Diese Erklärung gilt für die Website sprossa.de, die Anmeldung zur
        Beta-Warteliste und die Sprossa-Anwendung (nachfolgend gemeinsam
        „Sprossa“). Sie beschreibt, welche Daten tatsächlich verarbeitet werden –
        nicht mehr und nicht weniger.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">1. Verantwortlicher</h2>
      <p>Verantwortlich für die Datenverarbeitung ist:</p>
      <address className="not-italic mt-2">
        The Oaktree, Inhaber Sebastian Westhoff<br />
        Ickerner Heide 4a<br />
        45731 Waltrop<br />
        Deutschland<br />
        E-Mail:{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
      </address>
      <p className="mt-2">
        Anfragen zu dieser Erklärung und zu Ihren Rechten richten Sie bitte an
        diese E-Mail-Adresse. Sollte die Bestellung eines
        Datenschutzbeauftragten gesetzlich erforderlich sein, benennen wir
        diese Person und ergänzen ihre Kontaktdaten an dieser Stelle.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">2. Überblick</h2>
      <p>
        Wir verarbeiten personenbezogene Daten nur, soweit das für den Betrieb
        der Website, die Verwaltung der Warteliste und die Bereitstellung der
        Anwendung erforderlich ist. Es gibt <strong>keinen Newsletter</strong>,
        keine Werbe- oder Analysedienste Dritter (kein Google Analytics, kein
        Meta-Pixel, keine Werbe-Cookies) und keinen Verkauf von Daten.
      </p>
      <p className="mt-2">
        Sprossa befindet sich in der Beta-Phase und wird unentgeltlich
        bereitgestellt. Eine Zahlungsabwicklung findet derzeit nicht statt.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">3. Hosting und Server-Logfiles</h2>
      <p>
        Website, Anwendung und Datenbank werden bei der{" "}
        <strong>Hetzner Online GmbH</strong>, Industriestr. 25, 91710
        Gunzenhausen, auf Servern in Deutschland betrieben. Mit Hetzner besteht
        ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO.
      </p>
      <p className="mt-2">
        Beim Aufruf unserer Seiten fallen technisch notwendige Logdaten an:
        IP-Adresse, Datum und Uhrzeit des Zugriffs, aufgerufene Adresse,
        übertragene Datenmenge, Statuscode, Referrer und User-Agent. Diese Daten
        dienen der Auslieferung der Seite, der Fehleranalyse und der Abwehr von
        Angriffen. Rechtsgrundlage ist unser berechtigtes Interesse an einem
        sicheren und stabilen Betrieb (Art. 6 Abs. 1 lit. f DSGVO). Die Logfiles
        werden gelöscht, sobald sie für diese Zwecke nicht mehr benötigt werden;
        eine Zusammenführung mit anderen Daten findet nicht statt.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">4. Warteliste (Beta-Anmeldung)</h2>
      <p>Für die Vormerkung zur Beta verarbeiten wir:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>E-Mail-Adresse (Pflichtfeld)</li>
        <li>optional: Name und Haushaltsgröße</li>
        <li>Zeitpunkt der Anmeldung, Bestätigungsstatus und Zeitpunkt der Bestätigung</li>
        <li>Herkunft der Anmeldung (Quelle und UTM-Kampagne, z.&nbsp;B. Pinterest oder Instagram)</li>
        <li>IP-Adresse, die bei der Bestätigung des Double-Opt-in-Links anfällt (Nachweis und Missbrauchsschutz)</li>
      </ul>
      <p className="mt-2">
        Die Anmeldung erfolgt im <strong>Double-Opt-in-Verfahren</strong>: Wir
        senden Ihnen eine E-Mail mit einem Bestätigungslink, der 48 Stunden
        gültig ist. Erst nach dem Klick gilt die Anmeldung als abgeschlossen.
        Ohne Bestätigung nehmen wir nicht am Beta-Betrieb teil.
      </p>
      <p className="mt-2">
        Rechtsgrundlage ist Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO). Sie
        können sie jederzeit über den Abmeldelink in der E-Mail oder per
        Nachricht an uns widerrufen. Bei Abmeldung löschen wir Ihren Eintrag
        unverzüglich; die Rechtmäßigkeit der bis dahin erfolgten Verarbeitung
        bleibt unberührt. Wir nutzen die Warteliste ausschließlich für
        Informationen zum Beta-Start – nicht für Werbung und nicht für einen
        Newsletter.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">5. Konto, Anmeldung und Passwort-Reset</h2>
      <p>Bei der Registrierung und bei der Anmeldung verarbeiten wir:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>E-Mail-Adresse</strong> und <strong>Anzeigename</strong></li>
        <li>
          <strong>Passwort</strong> – ausschließlich als gesalzener Hash
          (PBKDF2-HMAC-SHA256 mit individuellem Salt). Das Klartext-Passwort
          wird nicht gespeichert und ist für uns nicht lesbar.
        </li>
        <li>Zeitpunkt der Registrierung und Status des Kontos</li>
        <li>
          bei Passwort-Reset: ein Einmal-Token mit einer Stunde Gültigkeit, das
          nach der Nutzung ungültig wird
        </li>
      </ul>
      <p className="mt-2">
        Zur Aufrechterhaltung der Sitzung setzen wir das technisch notwendige
        Cookie <code>sprossa_token</code> (httpOnly, SameSite=Lax, Laufzeit 24
        Stunden). Es enthält ein signiertes Sitzungs-Token, keine Werbe- oder
        Tracking-Informationen, und wird beim Abmelden gelöscht.
      </p>
      <p className="mt-2">
        Rechtsgrundlage ist die Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)
        sowie für Sicherheitsmaßnahmen unser berechtigtes Interesse (Art. 6
        Abs. 1 lit. f DSGVO).
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">6. Haushalts-, Rezept- und Einkaufsdaten</h2>
      <p>
        Innerhalb der Anwendung speichern wir die von Ihnen eingegebenen Inhalte,
        damit Ihre Pläne erhalten bleiben:
      </p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Haushalt:</strong> Haushaltsname, Ernährungsprofil (Ernährungsform, Küchenrichtungen, Fokusthemen, Abneigungen)</li>
        <li><strong>Haushaltsmitglieder:</strong> Name, optional Alter und Gewicht (für die Portionsberechnung), Allergien und Unverträglichkeiten, Ernährungsziele, freie Notizen, Status aktiv/inaktiv</li>
        <li><strong>Rezepte:</strong> Titel, Beschreibung, Zutaten, Zubereitung, Portionen, Tags, Bild- und Quellenangaben</li>
        <li><strong>Pläne:</strong> Monats- und Wochenpläne, Mahlzeiten an Wochentagen, Portionsfaktoren, Wiederholungen, Notizen</li>
        <li><strong>Einkaufslisten:</strong> Zutaten, Mengen, Kategorien, abgehakte Positionen, Notizen</li>
      </ul>
      <p className="mt-2">
        Zweck ist ausschließlich die Erstellung, Anzeige und Verwaltung Ihrer
        Ernährungspläne, Rezepte und Einkaufslisten. Rechtsgrundlage ist die
        Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO). Eine Auswertung zu
        Werbezwecken oder eine Weitergabe an Dritte findet nicht statt.
      </p>
      <p className="mt-2">
        <strong>Hinweis zu Angehörigen:</strong> Wenn Sie Daten weiterer
        Haushaltsmitglieder eintragen, sind Sie dafür verantwortlich, dass diese
        damit einverstanden sind. Bei Kindern entscheiden die
        Erziehungsberechtigten.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">7. Allergien und Gesundheitsdaten (Art. 9 DSGVO)</h2>
      <p>
        Angaben zu Allergien und Unverträglichkeiten sind Gesundheitsdaten im
        Sinne von Art. 9 Abs. 1 DSGVO. Wir verarbeiten sie ausschließlich, um
        Rezepte und Pläne entsprechend zu filtern und zu kennzeichnen.
      </p>
      <p className="mt-2">
        Rechtsgrundlage ist Ihre <strong>ausdrückliche Einwilligung</strong> nach
        Art. 9 Abs. 2 lit. a DSGVO. Diese Einwilligung fragen wir im Onboarding
        gesondert ab, sobald Sie Allergien auswählen; der Zeitpunkt wird als
        Nachweis gespeichert. Ohne Einwilligung berücksichtigen wir keine
        Allergien – die übrige Nutzung bleibt möglich.
      </p>
      <p className="mt-2">
        Sie können die Einwilligung jederzeit im Profil widerrufen und die
        Allergieangaben dort löschen. Alternativ genügt eine E-Mail an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
        ; wir löschen die Angaben dann unverzüglich. Der Nachweis über die
        Erteilung und den Widerruf der Einwilligung bleibt aus
        Rechenschaftsgründen erhalten. Die Rechtmäßigkeit der bis zum Widerruf
        erfolgten Verarbeitung bleibt unberührt.
      </p>
      <p className="mt-2">
        <strong>Wichtig:</strong> Die Angaben beruhen auf Ihrer Selbstauskunft.
        Sprossa ersetzt keine medizinische Beratung und keine Prüfung der
        Zutaten auf Spuren oder Kreuzkontaminationen. Prüfen Sie vor der
        Zubereitung stets die Angaben der Hersteller.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">8. Reichweitenmessung der Landingpage</h2>
      <p>Beim Aufruf der Landingpage erfassen wir:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>aufgerufenen Pfad und Referrer</li>
        <li>UTM-Parameter (Quelle, Medium, Kampagne, Inhalt)</li>
        <li>Geräteklasse (mobil oder Desktop), abgeleitet aus dem User-Agent</li>
        <li>
          einen <strong>täglich wechselnden Besucher-Hash</strong>: SHA-256 aus
          IP-Adresse, User-Agent und Tagesdatum, gekürzt auf 32 Zeichen
        </li>
      </ul>
      <p className="mt-2">
        Die IP-Adresse wird nur zur Bildung dieses Hashs im Arbeitsspeicher
        verwendet und <strong>nicht gespeichert</strong>. Der Hash lässt sich
        wegen des täglichen Wechsels nicht über Tage hinweg zuordnen. Wir setzen
        dafür <strong>keine Cookies</strong> und kein Fingerprinting ein; die
        Daten werden nicht an Dritte übermittelt und nicht mit Ihrem Konto
        verknüpft.
      </p>
      <p className="mt-2">
        Zweck ist die Messung, welche Kanäle tatsächlich Besucher bringen.
        Rechtsgrundlage ist unser berechtigtes Interesse an einer datensparsamen
        Reichweitenmessung (Art. 6 Abs. 1 lit. f DSGVO). Die Pageview-Daten
        werden spätestens nach 90 Tagen gelöscht. Da keine Informationen auf
        Ihrem Endgerät gespeichert oder ausgelesen werden, ist eine Einwilligung
        nach § 25 Abs. 1 TDDDG nicht erforderlich.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">9. Cookies und lokale Speicherung</h2>
      <p>Wir verwenden ausschließlich technisch notwendige Speicherung:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li>
          <strong>Cookie <code>sprossa_token</code></strong> – hält die
          Anmeldung für 24 Stunden (httpOnly, SameSite=Lax).
        </li>
        <li>
          <strong><code>sessionStorage</code>, Schlüssel <code>sprossa_pv</code></strong>{" "}
          – verhindert, dass derselbe Seitenaufruf im selben Tab mehrfach
          gezählt wird. Wird beim Schließen des Tabs gelöscht.
        </li>
        <li>
          <strong><code>localStorage</code>, Schlüssel <code>grocery_checked_*</code></strong>{" "}
          – merkt sich auf Ihrem Gerät, welche Positionen der Einkaufsliste Sie
          abgehakt haben. Diese Information liegt nur lokal bei Ihnen und wird
          nicht an unseren Server übertragen.
        </li>
      </ul>
      <p className="mt-2">
        Rechtsgrundlage für diese Speicherung ist § 25 Abs. 2 Nr. 2 TDDDG
        (unbedingt erforderlich) sowie für die Anmeldung Art. 6 Abs. 1 lit. b
        DSGVO. Ein Cookie-Banner ist deshalb nicht erforderlich. Sie können
        lokale Speicherung in Ihren Browser-Einstellungen jederzeit löschen;
        dadurch gehen lediglich abgehakte Positionen und die Anmeldung verloren.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">10. Schriftarten</h2>
      <p>
        Die Schriftarten „Nunito“ und „Fraunces“ werden <strong>von unseren
        eigenen Servern</strong> ausgeliefert. Beim Aufruf unserer Seiten wird
        keine Verbindung zu Google oder einem anderen Schriftarten-Dienst
        aufgebaut; es werden dabei keine Daten an Dritte übermittelt.
      </p>
      <p className="mt-2">
        Die Dateien liegen als Webfonts auf demselben Server wie die Website.
        Rechtsgrundlage für die lokale Auslieferung ist unser berechtigtes
        Interesse an einer einheitlichen und performanten Darstellung
        (Art. 6 Abs. 1 lit. f DSGVO); personenbezogene Daten werden dabei
        nicht zusätzlich verarbeitet.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">11. E-Mail-Versand</h2>
      <p>
        Transaktionsmails (Wartelisten-Bestätigung, Passwort-Reset) versenden wir
        über die STRATO GmbH, Otto-Ostrowski-Straße 7, 10249 Berlin
        (SMTP <code>smtp.strato.de</code>). Dabei werden Ihre E-Mail-Adresse und
        der Inhalt der Nachricht verarbeitet. Mit STRATO besteht ein Vertrag zur
        Auftragsverarbeitung nach Art. 28 DSGVO. Rechtsgrundlage ist die
        Vertragserfüllung bzw. die Einwilligung für die Warteliste. Es werden
        keine Werbe- oder Newsletter-Mails versendet.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">12. Empfänger und Auftragsverarbeiter</h2>
      <p>Daten erhalten nur Stellen, die sie zur Erbringung des Dienstes benötigen:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Hetzner Online GmbH</strong> – Hosting von Anwendung und Datenbank (Deutschland)</li>
        <li><strong>STRATO GmbH</strong> – E-Mail-Versand</li>
        <li><strong>Google Ireland Limited</strong> – Auslieferung der Schriftarten (siehe Abschnitt 10)</li>
      </ul>
      <p className="mt-2">
        Eine Weitergabe zu Werbezwecken, ein Verkauf von Daten oder eine
        Übermittlung an Auskunfteien findet nicht statt. Eine gesetzliche
        Pflicht zur Herausgabe besteht nur gegenüber zuständigen Behörden und
        Gerichten.
      </p>
      <p className="mt-2">
        <strong>Zahlungen:</strong> In der Beta fallen keine Kosten an; es werden
        keine Zahlungsdaten erhoben. Für eine spätere kostenpflichtige Nutzung
        ist eine Abwicklung über Stripe vorgesehen. Darüber informieren wir
        rechtzeitig vorher und ergänzen diese Erklärung.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">13. Übermittlung in Drittländer</h2>
      <p>
        Die Verarbeitung findet grundsätzlich in der EU statt. Eine Übermittlung
        in die USA ist nur im Zusammenhang mit der Auslieferung der Google
        Fonts möglich (Abschnitt 10) und dort auf das EU-US Data Privacy
        Framework gestützt. Im Übrigen findet keine Übermittlung in Drittländer
        statt.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">14. Speicherdauer</h2>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Server-Logfiles:</strong> nur so lange, wie es für Betrieb, Fehleranalyse und Angriffabwehr erforderlich ist</li>
        <li><strong>Warteliste:</strong> bis zum Widerruf; ohne Einladung in die Beta löschen wir den Eintrag spätestens 12 Monate nach Ende der Beta-Phase</li>
        <li><strong>Bestätigungs- und Reset-Token:</strong> 48 Stunden bzw. eine Stunde, danach ungültig</li>
        <li><strong>Konto, Haushalts- und Plandaten:</strong> bis zur Löschung des Kontos; danach Löschung innerhalb von 30 Tagen</li>
        <li><strong>Sicherungskopien:</strong> rollierend, Löschung spätestens nach 30 Tagen</li>
        <li><strong>Reichweitenmessung:</strong> spätestens 90 Tage</li>
        <li><strong>Lokale Speicherung im Browser:</strong> bis Sie sie löschen; das Sitzungs-Cookie läuft nach 24 Stunden ab</li>
      </ul>
      <p className="mt-2">
        Sie können die Löschung Ihres Kontos jederzeit per E-Mail an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>{" "}
        verlangen. Wir löschen dann alle zugehörigen Daten; gesetzliche
        Aufbewahrungspflichten (etwa für Rechnungen bei kostenpflichtiger
        Nutzung) bleiben hiervon unberührt.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">15. Datensicherheit</h2>
      <p>
        Die Übertragung erfolgt verschlüsselt über HTTPS (TLS). Zugriffe auf die
        Datenbank sind auf den Anwendungsserver beschränkt. Passwörter werden
        nur als gesalzene Hashes gespeichert, das Sitzungs-Cookie ist für
        Skripte unlesbar (httpOnly). Zugang zum internen Statistik-Dashboard
        haben nur berechtigte Personen über eine passwortgeschützte
        Zugriffskontrolle. Wir prüfen diese Maßnahmen regelmäßig und passen sie
        an den Stand der Technik an.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">16. Ihre Rechte</h2>
      <p>Sie haben nach der DSGVO das Recht auf:</p>
      <ul className="list-disc pl-5 space-y-1 mt-2">
        <li><strong>Auskunft</strong> über die zu Ihnen gespeicherten Daten (Art. 15)</li>
        <li><strong>Berichtigung</strong> unrichtiger oder unvollständiger Daten (Art. 16)</li>
        <li><strong>Löschung</strong> (Art. 17, „Recht auf Vergessenwerden“)</li>
        <li><strong>Einschränkung der Verarbeitung</strong> (Art. 18)</li>
        <li><strong>Datenübertragbarkeit</strong> in einem gängigen Format (Art. 20)</li>
        <li><strong>Widerspruch</strong> gegen Verarbeitungen auf Grundlage berechtigter Interessen (Art. 21)</li>
        <li><strong>Widerruf einer Einwilligung</strong> jederzeit mit Wirkung für die Zukunft (Art. 7 Abs. 3)</li>
      </ul>
      <p className="mt-2">
        Zur Ausübung genügt eine E-Mail an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
        . Wir antworten innerhalb eines Monats; bei komplexen Anfragen kann diese
        Frist um zwei weitere Monate verlängert werden, worüber wir Sie
        informieren.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">17. Keine automatisierte Entscheidungsfindung</h2>
      <p>
        Pläne und Rezeptvorschläge werden automatisch aus Ihren Angaben
        erzeugt. Diese Vorschläge haben keine rechtliche Wirkung und treffen
        keine Entscheidung über Sie im Sinne von Art. 22 DSGVO; Sie können jeden
        Vorschlag ändern oder löschen.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">18. Beschwerderecht</h2>
      <p>
        Sie können sich bei einer Datenschutz-Aufsichtsbehörde beschweren,
        insbesondere bei der Behörde Ihres Wohnsitzes oder unseres Sitzes. Für
        uns zuständig ist die{" "}
        <strong>
          Landesbeauftragte für Datenschutz und Informationsfreiheit
          Nordrhein-Westfalen
        </strong>
        , Kavalleriestraße 2–4, 40213 Düsseldorf.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">19. Änderungen dieser Erklärung</h2>
      <p>
        Wir passen diese Erklärung an, wenn sich die Verarbeitung ändert – etwa
        beim Start der kostenpflichtigen Version oder beim Wechsel von
        Dienstleistern. Es gilt jeweils die hier veröffentlichte Fassung.
      </p>

      <hr className="mt-10 border-sprossa-ink/12" />
      <p className="text-sm text-sprossa-muted-strong">Stand: November 2026</p>
      <div className="mt-6">
        <Link href="/" className="font-semibold text-sprossa-green underline">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}
