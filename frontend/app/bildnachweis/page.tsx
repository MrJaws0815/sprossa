import Link from "next/link";

import { FOOD_CREDITS } from "../../lib/food-credits";

/**
 * Bildnachweis für die Rezeptfotos.
 *
 * Die Bilder stammen aus Wikimedia Commons und Flickr und stehen unter
 * CC0, CC BY oder CC BY-SA. Bei BY und BY-SA ist die Namensnennung Pflicht,
 * deshalb steht hier zu jedem Bild der Urheber samt Lizenz und Quell-Link.
 * Die Liste wird aus scripts/build_food_credits.py erzeugt.
 */
export default function BildnachweisPage() {
  const mitNennung = FOOD_CREDITS.filter((c) => c.lizenz !== "CC0");

  return (
    <article className="mx-auto max-w-[820px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Bildnachweis</h1>

      <p className="text-sprossa-muted-strong mb-2">
        Die Rezeptfotos in der Sprossa-App stammen aus freien Bildarchiven
        (Wikimedia Commons und Flickr) und stehen unter Creative-Commons-Lizenzen.
        Bei den Lizenzen <strong>CC BY</strong> und <strong>CC BY-SA</strong> ist
        die Namensnennung des Urhebers Pflicht — dieser Seite kommen wir damit
        nach. Bilder unter <strong>CC0</strong> sind gemeinfrei und benötigen
        keine Nennung; sie sind der Vollständigkeit halber ebenfalls aufgeführt.
      </p>

      <p className="text-sprossa-muted-strong mb-6">
        Insgesamt {FOOD_CREDITS.length} Bilder, davon {mitNennung.length} mit
        Namensnennungspflicht. Die Bilder wurden für die Darstellung
        zugeschnitten und komprimiert; sonst wurden sie nicht verändert. Ein
        Anspruch auf die abgebildeten Gerichte besteht nicht — die Fotos
        illustrieren, sie zeigen nicht zwingend das gekochte Ergebnis.
      </p>

      <div className="rounded-xl border border-sprossa-ink/10 bg-white p-5 mb-8">
        <p className="text-sm text-sprossa-muted-strong">
          <strong>Lizenzhinweis:</strong> Der volle Lizenztext ist unter{" "}
          <a
            href="https://creativecommons.org/licenses/"
            target="_blank"
            rel="noreferrer"
            className="font-semibold text-sprossa-green underline"
          >
            creativecommons.org/licenses
          </a>{" "}
          einsehbar. Fragen zu einzelnen Bildern beantworten wir unter{" "}
          <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
            hallo@sprossa.de
          </a>.
        </p>
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-sprossa-ink/15 text-left">
            <th className="py-2 pr-3 font-bold">Gericht</th>
            <th className="py-2 pr-3 font-bold">Foto</th>
            <th className="py-2 pr-3 font-bold">Lizenz</th>
            <th className="py-2 font-bold">Quelle</th>
          </tr>
        </thead>
        <tbody>
          {FOOD_CREDITS.map((c, i) => (
            <tr key={`${c.rezept}-${i}`} className="border-b border-sprossa-ink/5 align-top">
              <td className="py-2 pr-3">{c.rezept}</td>
              <td className="py-2 pr-3">{c.foto}</td>
              <td className="py-2 pr-3 whitespace-nowrap">
                {c.lizenz}
                {c.version ? ` ${c.version}` : ""}
              </td>
              <td className="py-2">
                {c.url ? (
                  <a
                    href={c.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sprossa-green underline"
                  >
                    {c.quelle || "Quelle"}
                  </a>
                ) : (
                  <span className="text-sprossa-muted">{c.quelle}</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <hr className="my-8 border-sprossa-ink/10" />

      <p className="text-sm text-sprossa-muted-strong">
        Siehe auch{" "}
        <Link href="/impressum" className="font-semibold text-sprossa-green underline">
          Impressum
        </Link>{" "}
        und{" "}
        <Link href="/datenschutz" className="font-semibold text-sprossa-green underline">
          Datenschutzerklärung
        </Link>
        .
      </p>
    </article>
  );
}
