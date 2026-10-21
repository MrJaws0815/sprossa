"use client";
import Link from "next/link";

export default function PlanPage() {
  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>
      <h1 className="mb-6 text-3xl font-bold">📅 Monatsplan – April 2025</h1>

      {/* Wochen-Navigation */}
      <div className="mb-8 flex gap-2">
        {[1, 2, 3, 4].map((w) => (
          <button
            key={w}
            className={`rounded-lg px-4 py-2 text-sm ${
              w === 1
                ? "bg-sprossa-green text-white"
                : "border border-gray-300 text-gray-700"
            }`}
          >
            Woche {w}
          </button>
        ))}
      </div>

      {/* Woche 1 - Detail */}
      <div className="rounded-lg border border-gray-200 p-4">
        <h2 className="mb-3 text-xl font-semibold">Woche 1 – ab 01.04.</h2>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="pb-2 font-semibold">Tag</th>
              <th className="pb-2 font-semibold">Abendessen</th>
              <th className="pb-2 font-semibold">Cook Once?</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Montag", "Nudeln mit Tomatensoße", "✅"],
              ["Dienstag", "Kartoffel-Gratin", "—"],
              ["Mittwoch", "Nudeln mit Tomatensoße 🔄", "✅ (Repeat)"],
              ["Donnerstag", "Hähnchen mit Reis", "—"],
              ["Freitag", "Gemüse-Pfanne", "—"],
              ["Samstag", "Kartoffel-Gratin 🔄", "✅ (Repeat)"],
              ["Sonntag", "Reste-Essen", "—"],
            ].map(([tag, essen, cookOnce]) => (
              <tr key={tag} className="border-b border-gray-100">
                <td className="py-2 font-medium">{tag}</td>
                <td className="py-2">{essen}</td>
                <td className="py-2">{cookOnce}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-xs text-gray-400">
          🔄 = Cook Once, Eat Twice – nur einmal kochen, am 2. Tag genießen.
        </p>
      </div>
    </section>
  );
}