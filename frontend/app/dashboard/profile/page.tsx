"use client";
import Link from "next/link";

export default function ProfilePage() {
  // Wir laden/speichern den Token aus localStorage (wird beim Login gesetzt)
  const TOKEN_KEY = "sprossa_token";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100/api/v1";

  let householdId: string | null = null;
  let householdName = "Mein Haushalt";
  let members: { id: string; name: string; age: number | null }[] = [];
  let newMemberName = "";
  let newMemberAge: number | null = null;

  async function loadHousehold() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
      // User abrufen
      const me = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!me.ok) return;
      const userData = await me.json();

      // Households des Users laden (über get_all auf households)
      const hhRes = await fetch(`${API_BASE}/households/${userData.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Fallback: Da user_id != household_id, laden wir über den Filter
      const allHh = await fetch(`${API_BASE}/households`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (allHh.ok) {
        const hhList = await allHh.json();
        if (hhList.length > 0) {
          const hh = hhList[0];
          householdId = hh.id;
          householdName = hh.name;
          // Members laden
          const membersRes = await fetch(`${API_BASE}/households/${hh.id}/members`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (membersRes.ok) {
            members = await membersRes.json();
          }
        }
      }
    } catch (e) {
      console.error("Fehler beim Laden des Households", e);
    }
  }

  async function saveHousehold() {
    if (!householdId) return;
    const token = localStorage.getItem(TOKEN_KEY);
    await fetch(`${API_BASE}/households/${householdId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name: householdName }),
    });
  }

  async function addMember() {
    if (!householdId || !newMemberName) return;
    const token = localStorage.getItem(TOKEN_KEY);
    await fetch(`${API_BASE}/households/${householdId}/members`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name: newMemberName, age: newMemberAge }),
    });
    newMemberName = "";
    newMemberAge = null;
    loadHousehold();
  }

  async function removeMember(mid: string) {
    if (!householdId) return;
    const token = localStorage.getItem(TOKEN_KEY);
    await fetch(`${API_BASE}/households/${householdId}/members/${mid}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    loadHousehold();
  }

  // Initial laden
  if (typeof window !== "undefined") {
    loadHousehold();
  }

  return (
    <section className="py-8">
      <div className="mb-4">
        <Link href="/dashboard" className="text-sprossa-green text-sm">
          ← Zurück zum Dashboard
        </Link>
      </div>
      <h1 className="mb-6 text-3xl font-bold">👤 Profil – {householdName}</h1>

      {/* Household-Name ändern */}
      <div className="mb-8 rounded-lg border border-gray-200 p-6">
        <h2 className="mb-4 text-xl font-semibold">🏠 Haushalt</h2>
        <div className="space-y-3">
          <label className="block mb-1 text-sm font-medium">Name des Haushalts</label>
          <input
            type="text"
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            value={householdName}
            onChange={(e) => { householdName = e.target.value; }}
          />
          <button
            onClick={saveHousehold}
            className="rounded-lg bg-sprossa-green px-4 py-2 text-sm text-white"
          >
            Speichern
          </button>
        </div>
      </div>

      {/* Members */}
      <div className="mb-8 rounded-lg border border-gray-200 p-6">
        <h2 className="mb-4 text-xl font-semibold">👨‍👩‍👧‍👦 Mitglieder</h2>

        {/* Bestehende Members */}
        <ul className="space-y-2">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between border-b border-gray-100 pb-2">
              <span className="font-medium">{m.name}{m.age ? ` (${m.age} J.)` : ""}</span>
              <button
                onClick={() => removeMember(m.id)}
                className="rounded bg-sprossa-error px-3 py-1 text-xs text-white"
              >
                Entfernen
              </button>
            </li>
          ))}
        </ul>

        {/* Neues Member hinzufügen */}
        <div className="mt-4 border-t border-gray-200 pt-4">
          <h3 className="mb-2 font-semibold text-md">Mitglied hinzufügen</h3>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Name"
              className="rounded-lg border border-gray-300 px-3 py-2"
              value={newMemberName}
              onChange={(e) => { newMemberName = e.target.value; }}
            />
            <input
              type="number"
              placeholder="Alter"
              className="w-20 rounded-lg border border-gray-300 px-3 py-2"
              value={newMemberAge || ""}
              onChange={(e) => { newMemberAge = parseInt(e.target.value) || null; }}
            />
            <button
              onClick={addMember}
              className="rounded-lg bg-sprossa-green px-4 py-2 text-sm text-white"
            >
              Hinzufügen
            </button>
          </div>
        </div>
      </div>

      {/* Token-Info */}
      <div className="mb-8 rounded-lg border border-gray-200 p-6">
        <h2 className="mb-4 text-xl font-semibold">🔑 API-Zugang</h2>
        <p className="mb-2 text-sm text-gray-600">
          Dein Token wird im Browser gespeichert. 
          {typeof window !== "undefined" && localStorage.getItem(TOKEN_KEY)
            ? "✅ Token vorhanden"
            : "❌ Kein Token – bitte einloggen"}
        </p>
      </div>
    </section>
  );
}