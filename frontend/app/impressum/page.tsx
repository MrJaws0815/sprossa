import Link from "next/link";

export default function ImpressumPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Impressum</h1>

      <h2 className="text-xl font-bold mt-6 mb-3">Angaben gemäß § 5 DDG</h2>

      <p><strong>The Oaktree</strong></p>
      <p className="text-sprossa-muted-strong">Inhaber: Sebastian Westhoff</p>
      <address className="not-italic mt-1">
        Ickerner Heide 4a<br />
        45731 Waltrop<br />
        Deutschland
      </address>

      <h2 className="text-xl font-bold mt-6 mb-3">Kontakt</h2>
      <p>
        E-Mail:{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
      </p>
      <p className="mt-2 text-sprossa-muted-strong">
        Sprossa ist ein reines Online-Angebot. Für eine schnelle elektronische
        Kontaktaufnahme und unmittelbare Kommunikation genügt die oben genannte
        E-Mail-Adresse; eine Telefonnummer wird daher nicht angegeben. Wir
        bemühen uns, Anfragen innerhalb von zwei Werktagen zu beantworten.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">Umsatzsteuer-ID</h2>
      <p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: DE335535698</p>

      <h2 className="text-xl font-bold mt-6 mb-3">Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
      <p>Sebastian Westhoff, Ickerner Heide 4a, 45731 Waltrop</p>

      <h2 className="text-xl font-bold mt-6 mb-3">Hosting</h2>
      <p>
        Website und Anwendung werden bei der Hetzner Online GmbH,
        Industriestr. 25, 91710 Gunzenhausen, betrieben. Die eingesetzten
        Server stehen in Deutschland (Rechenzentrum Falkenstein, Sachsen). Mit
        dem Anbieter besteht ein Vertrag zur Auftragsverarbeitung gemäß Art. 28
        DSGVO.
      </p>
      <p className="mt-2">
        Der Versand von Transaktions-E-Mails erfolgt über die STRATO GmbH,
        Otto-Ostrowski-Straße 7, 10249 Berlin.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">Verbraucherstreitbeilegung</h2>
      <p>
        Wir sind nicht verpflichtet und nicht bereit, an
        Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
        teilzunehmen. Bei Problemen wenden Sie sich bitte direkt an{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
        ; wir finden in der Regel eine Lösung.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">Haftung für Inhalte und Links</h2>
      <p>
        Als Diensteanbieter sind wir für eigene Inhalte auf diesen Seiten nach
        den allgemeinen Gesetzen verantwortlich. Wir sind jedoch nicht
        verpflichtet, übermittelte oder gespeicherte fremde Informationen zu
        überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige
        Tätigkeit hinweisen.
      </p>
      <p className="mt-2">
        Unser Angebot enthält Links zu externen Websites Dritter, auf deren
        Inhalte wir keinen Einfluss haben. Für diese fremden Inhalte übernehmen
        wir keine Gewähr; verantwortlich ist stets der jeweilige Anbieter. Zum
        Zeitpunkt der Verlinkung waren keine Rechtsverstöße erkennbar. Bei
        Bekanntwerden von Rechtsverstößen entfernen wir solche Links
        unverzüglich.
      </p>

      <h2 className="text-xl font-bold mt-6 mb-3">Urheberrecht</h2>
      <p>
        Die auf dieser Website erstellten Inhalte und Werke – insbesondere
        Texte, Rezepte, Grafiken und das Design – unterliegen dem deutschen
        Urheberrecht. Vervielfältigung, Bearbeitung und Verbreitung außerhalb
        der Grenzen des Urheberrechts bedürfen unserer schriftlichen Zustimmung.
        Downloads und Kopien dieser Seite sind nur für den privaten, nicht
        kommerziellen Gebrauch gestattet.
      </p>

      <hr className="mt-10 border-sprossa-ink/12" />
      <p className="text-sm text-sprossa-muted-strong">Stand: November 2026</p>
      <div className="mt-6">
        <Link href="/" className="text-sprossa-green">← Zurück zur Startseite</Link>
      </div>
    </article>
  );
}
