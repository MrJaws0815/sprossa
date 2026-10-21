import Link from "next/link";

export default function FeaturesPage() {
  return (
    <section className="py-12">
      <h1 className="mb-6 text-3xl font-bold">🌱 Sprossa – Funktionen</h1>
      <p className="mb-6 text-gray-600 text-lg">
        Dein Familien-Ernährungsplan. Einen Monat voraus.
      </p>
      <ul className="space-y-4 text-lg">
        <li>
          <strong>Monatsplan-Generator</strong> – Automatische Erstellung
          von Ernährungsplänen für 4–5 Wochen, abgestimmt auf deine Familie.
        </li>
        <li>
          <strong>Cook Once, Eat Twice</strong> – Kluge Doppel-Koch-Strategie:
          einmal kochen, zweimal essen. Reduziert Koch-Aufwand um bis zu 40 %.
        </li>
        <li>
          <strong>Smarte Einkaufsliste</strong> – Alle Zutaten aus dem Plan
          automatisch summiert, nach Supermarkt-Gängen gruppiert.
        </li>
        <li>
          <strong>Familien-Profile</strong> – Erwachsene und
          Kinder mit Allergien, Vorlieben und Ernährungszielen.
        </li>
        <li>
          <strong>Rezept-Bibliothek</strong> – Eigene Rezepte verwalten,
          mit Mengenangaben und Substitutions-Vorschlägen.
        </li>
        <li>
          <strong>Substitutions-Engine</strong> – Automatischer Austausch
          von Zutaten bei Allergien oder nach Saison.
        </li>
      </ul>
      <div className="mt-8">
        <Link
          href="/register"
          className="rounded-lg bg-sprossa-green px-6 py-2 text-white"
        >
          Jetzt starten
        </Link>
      </div>
    </section>
  );
}