import Link from "next/link";

export default function AgbPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Allgemeine Geschäftsbedingungen (AGB)</h1>

      <p className="text-sprossa-muted-strong mb-4">
        Sprossa befindet sich in der kostenlosen Beta-Phase. Es entsteht kein
        entgeltlicher Vertrag; ein gesetzliches Widerrufsrecht besteht daher derzeit
        nicht. Die Widerrufsbelehrung in § 8 gilt ab der kostenpflichtigen Version.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 1 Geltungsbereich</h2>
      <p>
        Diese Bedingungen gelten für die Nutzung von Sprossa, einem Dienst zur
        Erstellung monatlicher Familien-Ernährungspläne einschließlich Rezepten und
        Einkaufslisten, betrieben von The Oaktree, Inhaber Sebastian Westhoff,
        Ickerner Heide 4a, 45731 Waltrop.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 2 Leistungsbeschreibung</h2>
      <p>
        (1) Sprossa erstellt auf Grundlage Ihrer Angaben Vorschläge für Monatspläne,
        Rezepte und Einkaufslisten. Der Dienst befindet sich in der Beta-Phase und wird
        kostenlos bereitgestellt.
      </p>
      <p className="mt-2">
        (2) Ein Anspruch auf ständige Verfügbarkeit besteht nicht. Wartungsarbeiten und
        Weiterentwicklungen können zu Einschränkungen führen.
      </p>
      <p className="mt-2">
        (3) Funktionsumfang und Preise der späteren kostenpflichtigen Version werden
        rechtzeitig vor deren Start bekannt gegeben.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 3 Registrierung und Konto</h2>
      <p>
        (1) Für die Nutzung ist ein Konto erforderlich. Ihre Angaben müssen
        wahrheitsgemäß sein; das Passwort ist geheim zu halten.
      </p>
      <p className="mt-2">
        (2) Sie können Ihr Konto jederzeit löschen. Wir behalten uns vor, Konten bei
        Verstößen gegen diese Bedingungen zu sperren.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 4 Nutzungsrechte</h2>
      <p>
        Wir räumen Ihnen ein einfaches, nicht übertragbares Recht ein, den Dienst für
        private Zwecke zu nutzen. Rezepte und Pläne dürfen für den eigenen Haushalt
        verwendet, aber nicht kommerziell weiterverbreitet werden.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 5 Pflichten und Hinweise des Nutzers</h2>
      <p>
        (1) <strong>Allergien und Unverträglichkeiten:</strong> Die Filterung beruht
        ausschließlich auf Ihren eigenen Angaben. Prüfen Sie vor der Zubereitung stets
        die Zutatenlisten der Produkte.
      </p>
      <p className="mt-2">
        (2) <strong>Keine medizinische Beratung:</strong> Sprossa ersetzt keine
        ernährungs- oder medizinisch-therapeutische Beratung.
      </p>
      <p className="mt-2">
        (3) <strong>Keine Garantie auf Vollständigkeit:</strong> Rezeptdaten werden mit
        Sorgfalt gepflegt, können aber Fehler enthalten.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 6 Haftung</h2>
      <p>
        (1) Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit sowie bei
        Verletzung von Leben, Körper oder Gesundheit.
      </p>
      <p className="mt-2">
        (2) Bei einfacher Fahrlässigkeit haften wir nur für die Verletzung wesentlicher
        Vertragspflichten und begrenzt auf den vorhersehbaren, vertragstypischen
        Schaden.
      </p>
      <p className="mt-2">
        (3) Eine Haftung für die Richtigkeit ernährungsbezogener Empfehlungen im
        Einzelfall ist ausgeschlossen, soweit gesetzlich zulässig.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 7 Änderungen und Beendigung</h2>
      <p>
        (1) Wir können diese Bedingungen mit Wirkung für die Zukunft ändern, wenn
        sachliche Gründe vorliegen. Änderungen kündigen wir mindestens vier Wochen
        vorher an.
      </p>
      <p className="mt-2">
        (2) Die Beta kann jederzeit beendet werden. Wir kündigen dies mindestens
        14 Tage vorher per E-Mail an.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 8 Widerrufsrecht</h2>
      <p>
        Verbraucher haben bei entgeltlichen Verträgen ein vierzehntägiges
        Widerrufsrecht. Die vollständige Widerrufsbelehrung samt Muster-Widerrufsformular
        veröffentlichen wir vor dem Start der kostenpflichtigen Version.
      </p>
      <p className="mt-2">
        <strong>In der kostenlosen Beta besteht kein Widerrufsrecht</strong>, da keine
        entgeltliche Leistung erbracht wird.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">§ 9 Schlussbestimmungen</h2>
      <p>
        Es gilt deutsches Recht. Sollte eine Bestimmung unwirksam sein, bleibt der
        übrige Vertrag wirksam; an die Stelle der unwirksamen Regelung tritt die
        gesetzliche Bestimmung.
      </p>

      <hr className="mt-10 border-sprossa-ink/12" />
      <p className="text-sm text-sprossa-muted-strong">Stand: November 2026</p>
      <div className="mt-6">
        <Link href="/" className="font-semibold text-sprossa-green underline">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}
