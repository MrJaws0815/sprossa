import Link from "next/link";

export default function AgbPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Allgemeine Geschäftsbedingungen (AGB)</h1>

      <p className="text-sprossa-muted-strong mb-4">
        Sprossa befindet sich in der kostenlosen Beta-Phase. Die Nutzung ist
        derzeit unentgeltlich; es entstehen keine Kosten und keine
        Abo-Verpflichtung. Die Widerrufsbelehrung in § 12 gilt für die spätere
        kostenpflichtige Version.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 1 Geltungsbereich und Anbieter</h2>
      <p>
        (1) Diese Bedingungen gelten für die Nutzung von Sprossa, einem
        Online-Dienst zur Erstellung monatlicher Ernährungspläne für Familien
        einschließlich Rezepten und Einkaufslisten, sowie für die zugehörige
        Website und Warteliste.
      </p>
      <p className="mt-2">
        (2) Anbieter ist The Oaktree, Inhaber Sebastian Westhoff, Ickerner Heide
        4a, 45731 Waltrop, Deutschland (nachfolgend „wir“ oder „Sprossa“).
        Kontakt:{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
        .
      </p>
      <p className="mt-2">
        (3) Diese Bedingungen richten sich an Verbraucher im Sinne des § 13 BGB.
        Für Unternehmer gilt § 14 BGB; abweichende Bedingungen des Nutzers werden
        nicht Vertragsbestandteil, es sei denn, wir stimmen ausdrücklich
        schriftlich zu.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 2 Vertragsschluss</h2>
      <p>
        (1) Die Darstellung von Sprossa auf der Website ist kein rechtlich
        bindendes Angebot. Mit dem Absenden des Registrierungsformulars geben Sie
        ein Angebot auf Abschluss eines Nutzungsvertrags ab.
      </p>
      <p className="mt-2">
        (2) Der Vertrag kommt zustande, sobald wir Ihr Konto freischalten oder
        Ihnen die Nutzung ermöglichen. Eine gesonderte Bestätigung ist nicht
        erforderlich, wir senden jedoch eine Bestätigung an die angegebene
        E-Mail-Adresse.
      </p>
      <p className="mt-2">
        (3) Die Anmeldung zur Warteliste begründet keinen Nutzungsvertrag. Ein
        Anspruch auf Einladung in die Beta besteht nicht.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 3 Leistungsbeschreibung und Beta-Status</h2>
      <p>
        (1) Sprossa erstellt auf Grundlage Ihrer Angaben Vorschläge für
        Monats- und Wochenpläne, Rezepte und Einkaufslisten und stellt diese in
        einer Web-Anwendung bereit. Die Pläne beruhen auf Ihren Angaben zu
        Haushaltsgröße, Ernährungsform und Allergien.
      </p>
      <p className="mt-2">
        (2) <strong>Beta-Status:</strong> Der Dienst befindet sich in
        Entwicklung. Funktionen können sich ändern, eingeschränkt oder
        vorübergehend nicht verfügbar sein. Wir weisen ausdrücklich darauf hin,
        dass Fehler auftreten und Datenverluste möglich sind. Wir empfehlen,
        wichtige Inhalte zusätzlich zu sichern.
      </p>
      <p className="mt-2">
        (3) Ein Anspruch auf eine bestimmte Verfügbarkeit, Reaktionszeit oder
        einen bestimmten Funktionsumfang besteht in der Beta nicht. Wartung,
        Weiterentwicklung und Fehlerbehebung können zu Unterbrechungen führen;
        wir bemühen uns um Vorabinformationen, soweit zumutbar.
      </p>
      <p className="mt-2">
        (4) Funktionsumfang und Preise einer späteren kostenpflichtigen Version
        geben wir rechtzeitig vor deren Start bekannt. Eine automatische
        Umstellung von der kostenlosen Beta auf ein kostenpflichtiges Angebot
        findet nicht statt; hierfür ist Ihre ausdrückliche Zustimmung
        erforderlich.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 4 Preise und Zahlung</h2>
      <p>
        (1) Die Nutzung von Sprossa ist während der Beta-Phase{" "}
        <strong>kostenlos</strong>. Es fallen keine Gebühren, keine
        Mindestlaufzeit und keine automatische Verlängerung an.
      </p>
      <p className="mt-2">
        (2) Für die Beta erheben wir keine Zahlungsdaten. Sollte künftig eine
        kostenpflichtige Nutzung eingeführt werden, informieren wir vorab über
        Preise, Abrechnungszeitraum und Kündigungsfristen. Ohne Ihre Zustimmung
        entstehen keine Kosten.
      </p>
      <p className="mt-2">
        (3) Etwaige Gebühren verstehen sich als Endpreise einschließlich der
        gesetzlichen Umsatzsteuer.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 5 Registrierung, Konto und Pflichten</h2>
      <p>
        (1) Die Nutzung der Anwendung setzt ein Konto voraus. Sie müssen
        mindestens 18 Jahre alt und unbeschränkt geschäftsfähig sein.
      </p>
      <p className="mt-2">
        (2) Ihre Angaben müssen wahrheitsgemäß und vollständig sein. Sie sind
        verpflichtet, Ihre Zugangsdaten geheim zu halten und uns unverzüglich zu
        informieren, wenn Sie einen Missbrauch vermuten.
      </p>
      <p className="mt-2">
        (3) Das Konto ist nicht übertragbar. Eine Nutzung durch Dritte ohne Ihre
        Zustimmung ist untersagt; für Handlungen über Ihr Konto haften Sie nach
        den gesetzlichen Bestimmungen.
      </p>
      <p className="mt-2">
        (4) Sie können die Löschung Ihres Kontos jederzeit per E-Mail an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>{" "}
        verlangen. Wir löschen das Konto und die zugehörigen Daten innerhalb von
        30 Tagen, soweit keine gesetzlichen Aufbewahrungspflichten entgegenstehen.
      </p>
      <p className="mt-2">
        (5) Wir können Konten sperren oder löschen, wenn begründete Anhaltspunkte
        für einen Verstoß gegen diese Bedingungen oder für eine missbräuchliche
        Nutzung bestehen. Sie erhalten dazu eine Mitteilung; gesetzliche Rechte
        bleiben unberührt.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 6 Gesundheit, Allergien und Ernährungsinformationen</h2>
      <p>
        (1) <strong>Allergien und Unverträglichkeiten:</strong> Die Filterung
        beruht ausschließlich auf Ihren eigenen Angaben. Wir können nicht
        gewährleisten, dass Rezepte, Zutaten oder Fertigprodukte frei von
        Allergenen, Spuren oder Kreuzkontaminationen sind. Prüfen Sie vor der
        Zubereitung stets die Zutaten- und Allergenangaben der Hersteller.
      </p>
      <p className="mt-2">
        (2) <strong>Keine medizinische Beratung:</strong> Sprossa ersetzt keine
        ärztliche, ernährungsmedizinische oder therapeutische Beratung. Bei
        diagnostizierten Allergien, Erkrankungen, Schwangerschaft oder
        besonderen Ernährungsanforderungen wenden Sie sich bitte an Fachpersonal.
      </p>
      <p className="mt-2">
        (3) <strong>Keine Garantie auf Vollständigkeit:</strong> Rezept- und
        Nährwertangaben werden mit Sorgfalt gepflegt, können aber Fehler
        enthalten. Angaben zu Mengen, Portionen und Zubereitung sind
        Empfehlungen.
      </p>
      <p className="mt-2">
        (4) Sie tragen die Verantwortung für die Angaben, die Sie zu weiteren
        Haushaltsmitgliedern eintragen. Bei Kindern entscheiden die
        Erziehungsberechtigten.
      </p>
      <p className="mt-2">
        (5) <strong>Rezeptbilder:</strong> Die Fotos in der Anwendung sind
        KI-generiert und dienen ausschließlich der Illustration. Sie zeigen ein
        Gericht dieser Art, nicht zwingend das Ergebnis des jeweiligen Rezepts;
        Anrichte, Portionsgröße und Details können abweichen. Maßgeblich sind
        allein der Rezepttext mit Zutaten und Zubereitung. Einzelheiten nennt
        der <a href="/bildnachweis" className="font-semibold text-sprossa-green underline">
          Hinweis zu den Rezeptbildern
        </a>.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 7 Nutzungsrechte und Inhalte</h2>
      <p>
        (1) Wir räumen Ihnen ein einfaches, nicht übertragbares und nicht
        unterlizenzierbares Recht ein, Sprossa für private Zwecke Ihres
        Haushalts zu nutzen.
      </p>
      <p className="mt-2">
        (2) Rezepte, Pläne und Einkaufslisten dürfen für den eigenen Haushalt
        verwendet, gespeichert und ausgedruckt werden. Eine kommerzielle
        Weiterverbreitung, ein Weiterverkauf oder die öffentliche Bereitstellung
        der Inhalte – auch in Auszügen – ist ohne unsere Zustimmung nicht
        gestattet.
      </p>
      <p className="mt-2">
        (3) Inhalte, die Sie selbst einstellen (etwa eigene Rezepte oder
        Notizen), bleiben Ihre Inhalte. Sie räumen uns die zur Speicherung,
        Anzeige und Verarbeitung innerhalb der Anwendung erforderlichen Rechte
        ein. Wir nutzen diese Inhalte nicht für Werbung.
      </p>
      <p className="mt-2">
        (4) Die Rechte an der Anwendung, am Design, an den Texten und an den von
        uns erstellten Rezepten liegen bei uns oder unseren Lizenzgebern.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 8 Verfügbarkeit und Änderungen des Dienstes</h2>
      <p>
        (1) Wir bemühen uns um eine hohe Verfügbarkeit, schulden in der Beta
        jedoch keine bestimmte Erreichbarkeit. Geplante Wartungen führen wir
        möglichst außerhalb üblicher Nutzungszeiten durch.
      </p>
      <p className="mt-2">
        (2) Wir dürfen den Dienst weiterentwickeln und einzelne Funktionen
        ändern oder einstellen, soweit dies für Sie zumutbar ist. Wesentliche
        Einschränkungen kündigen wir mit angemessener Frist an.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 9 Haftung</h2>
      <p>
        (1) Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit, bei
        arglistigem Verschweigen eines Mangels, bei Übernahme einer Garantie
        sowie bei Verletzung von Leben, Körper oder Gesundheit.
      </p>
      <p className="mt-2">
        (2) Bei einfacher Fahrlässigkeit haften wir nur für die Verletzung
        wesentlicher Vertragspflichten (Kardinalpflichten) und begrenzt auf den
        vorhersehbaren, vertragstypischen Schaden. Wesentliche Pflichten sind
        solche, deren Erfüllung die ordnungsgemäße Durchführung des Vertrags
        überhaupt erst ermöglicht und auf deren Einhaltung Sie regelmäßig
        vertrauen dürfen.
      </p>
      <p className="mt-2">
        (3) Die Haftung nach dem Produkthaftungsgesetz sowie Ansprüche aus
        Garantien bleiben unberührt. Eine Haftung für die Richtigkeit
        ernährungsbezogener Empfehlungen im Einzelfall ist ausgeschlossen,
        soweit gesetzlich zulässig; § 6 bleibt maßgeblich.
      </p>
      <p className="mt-2">
        (4) Für Datenverluste haften wir nur für den Aufwand der
        Wiederherstellung, der bei ordnungsgemäßer und regelmäßiger
        Datensicherung durch Sie entstanden wäre.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 10 Laufzeit und Kündigung</h2>
      <p>
        (1) Der Nutzungsvertrag läuft auf unbestimmte Zeit und kann von beiden
        Seiten jederzeit ohne Frist gekündigt werden.
      </p>
      <p className="mt-2">
        (2) Ihre Kündigung erfolgt per E-Mail an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>{" "}
        oder über die Kontolöschung. Wir bestätigen den Zugang.
      </p>
      <p className="mt-2">
        (3) Wir können die Beta-Phase insgesamt beenden. Dies kündigen wir
        mindestens 14 Tage vorher per E-Mail an. Nach Beendigung löschen wir Ihre
        Daten nach den Fristen der Datenschutzerklärung; Sie können Ihre Daten
        vorher exportieren oder sichern.
      </p>
      <p className="mt-2">
        (4) Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt
        für beide Seiten unberührt.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 11 Änderungen dieser Bedingungen</h2>
      <p>
        (1) Wir können diese Bedingungen mit Wirkung für die Zukunft ändern, wenn
        sachliche Gründe vorliegen (etwa neue Funktionen, geänderte
        Rechtslage oder Preise). Änderungen kündigen wir mindestens vier Wochen
        vorher in Textform an.
      </p>
      <p className="mt-2">
        (2) Widersprechen Sie nicht innerhalb von vier Wochen nach Zugang der
        Mitteilung, gelten die Änderungen als angenommen. Auf diese Folge und
        Ihr Widerspruchsrecht weisen wir in der Mitteilung gesondert hin.
      </p>
      <p className="mt-2">
        (3) Für die kostenlose Beta bleiben Änderungen, die Ihre Nutzung
        wesentlich erschweren, jederzeit mit sofortiger Wirkung möglich, wenn
        Sie der Änderung nicht zustimmen; in diesem Fall können beide Seiten den
        Vertrag beenden.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 12 Widerrufsrecht für Verbraucher</h2>
      <p>
        <strong>Hinweis für die Beta:</strong> Die Nutzung ist unentgeltlich. Ein
        gesetzliches Widerrufsrecht besteht bei unentgeltlichen Verträgen nicht.
        Die folgende Belehrung gilt für die kostenpflichtige Version ab deren
        Start.
      </p>

      <h3 className="text-lg font-bold mt-4 mb-2">Widerrufsbelehrung</h3>
      <p>
        Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen
        Vertrag zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage ab dem
        Tag des Vertragsabschlusses.
      </p>
      <p className="mt-2">
        Um Ihr Widerrufsrecht auszuüben, müssen Sie uns
      </p>
      <address className="not-italic mt-2">
        The Oaktree, Inhaber Sebastian Westhoff<br />
        Ickerner Heide 4a, 45731 Waltrop, Deutschland<br />
        E-Mail: hallo@sprossa.de
      </address>
      <p className="mt-2">
        mittels einer eindeutigen Erklärung (zum Beispiel ein mit der Post
        versandter Brief oder eine E-Mail) über Ihren Entschluss, diesen Vertrag
        zu widerrufen, informieren. Sie können dafür das beigefügte
        Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist.
        Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung
        über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist
        absenden.
      </p>
      <p className="mt-2">
        <strong>Folgen des Widerrufs:</strong> Wenn Sie diesen Vertrag
        widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten
        haben, unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag
        zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf bei uns
        eingegangen ist. Für die Rückzahlung verwenden wir dasselbe
        Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt
        haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes
        vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte
        berechnet.
      </p>
      <p className="mt-2">
        Haben Sie verlangt, dass die Dienstleistung während der Widerrufsfrist
        beginnen soll, so haben Sie uns einen angemessenen Betrag zu zahlen, der
        dem Anteil der bis zu dem Zeitpunkt, zu dem Sie uns von der Ausübung des
        Widerrufsrechts unterrichten, bereits erbrachten Dienstleistungen im
        Vergleich zum Gesamtumfang der im Vertrag vorgesehenen Dienstleistungen
        entspricht.
      </p>
      <p className="mt-2">
        <strong>Vorzeitiges Erlöschen:</strong> Bei einem Vertrag über die
        Bereitstellung digitaler Inhalte erlischt das Widerrufsrecht, wenn wir
        mit der Ausführung begonnen haben, nachdem Sie ausdrücklich zugestimmt
        haben und Ihre Kenntnis davon bestätigt haben, dass Sie durch Ihre
        Zustimmung mit Beginn der Ausführung Ihr Widerrufsrecht verlieren (§ 356
        Abs. 5 BGB). Diese Zustimmung holen wir vor dem Start der
        kostenpflichtigen Nutzung gesondert ein.
      </p>

      <h3 className="text-lg font-bold mt-4 mb-2">Muster-Widerrufsformular</h3>
      <p className="text-sm">
        (Wenn Sie den Vertrag widerrufen wollen, füllen Sie dieses Formular aus
        und senden Sie es zurück.)
      </p>
      <div className="mt-2 rounded-xl border border-sprossa-ink/15 bg-white p-4 text-sm">
        <p>An: The Oaktree, Inhaber Sebastian Westhoff, Ickerner Heide 4a, 45731 Waltrop, E-Mail: hallo@sprossa.de</p>
        <p className="mt-2">
          Hiermit widerrufe(n) ich/wir den von mir/uns abgeschlossenen Vertrag
          über die Erbringung der folgenden Dienstleistung:
        </p>
        <p className="mt-2">______________________________________________</p>
        <p className="mt-2">Bestellt am / Vertrag geschlossen am: ______________________</p>
        <p className="mt-2">Name des/der Verbraucher(s): ____________________________</p>
        <p className="mt-2">Anschrift des/der Verbraucher(s): ________________________</p>
        <p className="mt-2">Unterschrift (nur bei Mitteilung auf Papier): ______________</p>
        <p className="mt-2">Datum: ______________________</p>
      </div>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 13 Streitbeilegung</h2>
      <p>
        Wir sind nicht verpflichtet und nicht bereit, an
        Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
        teilzunehmen. Bei Beschwerden wenden Sie sich bitte zunächst an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
        .
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 14 Schlussbestimmungen</h2>
      <p>
        (1) Es gilt deutsches Recht unter Ausschluss des UN-Kaufrechts. Gegenüber
        Verbrauchern gilt diese Rechtswahl nur, soweit dadurch der Schutz durch
        zwingende Bestimmungen des Staates Ihres gewöhnlichen Aufenthalts nicht
        entzogen wird.
      </p>
      <p className="mt-2">
        (2) Ist eine Bestimmung unwirksam oder unvollständig, bleibt der übrige
        Vertrag wirksam. An die Stelle der unwirksamen Bestimmung tritt die
        gesetzliche Regelung.
      </p>
      <p className="mt-2">
        (3) Gerichtsstand ist, soweit gesetzlich zulässig, unser Sitz. Für
        Verbraucher gilt die gesetzliche Zuständigkeit.
      </p>

      <hr className="mt-10 border-sprossa-ink/12" />
      <p className="text-sm text-sprossa-muted-strong">Stand: November 2026</p>
      <div className="mt-6">
        <Link href="/" className="font-semibold text-sprossa-green underline">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}
