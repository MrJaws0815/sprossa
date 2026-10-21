// TODO: Umleitung zur App nach Login
"use client";

export default function LoginPage() {
  return (
    <section className="py-12">
      <h1 className="mb-6 text-3xl font-bold">Anmelden</h1>
      <form className="mx-auto max-w-sm space-y-4">
        <div>
          <label className="block mb-1 text-sm font-medium">E-Mail</label>
          <input
            type="email"
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            placeholder="ich@familie.de"
          />
        </div>
        <div>
          <label className="block mb-1 text-sm font-medium">Passwort</label>
          <input
            type="password"
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
          />
        </div>
        <button
          type="submit"
          className="w-full rounded-lg bg-sprossa-green px-4 py-2 text-white hover:bg-sprossa-dark"
        >
          Anmelden
        </button>
      </form>
    </section>
  );
}