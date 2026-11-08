import Link from "next/link";

/**
 * Transparenzhinweis zu den Rezeptbildern.
 *
 * Die Fotos sind mit einem Diffusionsmodell (Stable Diffusion XL / RealVisXL)
 * erzeugt. Sie zeigen nicht zwingend das tatsächlich gekochte Gericht, sondern
 * illustrieren es. Der Hinweis steht hier, weil das Bildmaterial sonst den
 * Eindruck erwecken könnte, es sei eine Aufnahme des jeweiligen Rezepts.
 */
export default function BildnachweisPage() {
  return (
    <article className="mx-auto max-w-[720px] px-6 py-12 leading-relaxed text-sprossa-ink">
      <h1 className="font-display text-[32px] mb-6">Hinweis zu den Rezeptbildern</h1>

      <p className="text-sprossa-muted-strong mb-4">
        Die Rezeptfotos in der Sprossa-App sind <strong>KI-generiert</strong>.
        Sie wurden mit einem Bildgenerierungsmodell (Stable Diffusion XL,
        Fine-Tuning RealVisXL) erstellt und anschließend zugeschnitten.
      </p>

      <p className="text-sprossa-muted-strong mb-4">
        Die Bilder dienen der <strong>Illustration</strong>. Sie zeigen ein
        Gericht dieser Art, nicht zwingend das Ergebnis des jeweiligen Rezepts:
        Anrichte, Portionsgröße und Details können abweichen. Verbindlich ist
        immer der Rezepttext mit seinen Zutaten und Zubereitungsschritten.
      </p>

      <p className="text-sprossa-muted-strong mb-6">
        An den Bildern bestehen keine Rechte Dritter — es sind keine Fotos von
        Fotografinnen, Fotografen oder Bildagenturen. Sollten Sie ein Bild
        finden, das einer geschützten Aufnahme ungewöhnlich ähnlich sieht,
        melden Sie es uns bitte unter{" "}
        <a href="mailto:hallo@sprossa.de" className="font-semibold text-sprossa-green underline">
          hallo@sprossa.de
        </a>
        ; wir ersetzen es.
      </p>

      <div className="rounded-xl border border-sprossa-ink/10 bg-white p-5 mb-8">
        <p className="text-sm text-sprossa-muted-strong">
          <strong>Warum wir das offenlegen:</strong> Ein Foto weckt
          Erwartungen. Wenn ein Bild anders aussieht als das gekochte Gericht,
          soll niemand das Gefühl haben, getäuscht worden zu sein. Deshalb
          steht dieser Hinweis auch in unseren{" "}
          <Link href="/agb" className="font-semibold text-sprossa-green underline">
            AGB
          </Link>
          .
        </p>
      </div>

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
