# Rechtsseiten Sprossa – Überarbeitung November 2026

**Status:** Entwurf, nicht deployt. Änderungen nur im Repository.
**Nachtrag 06.11.:** Die technischen Lücken 1 (Google Fonts), 2 (JWT-Secret),
5 (Cookie `secure`) und 8 (AGB-Zustimmung bei Registrierung) sind behoben —
siehe Abschnitt 8. Offen bleiben Löschjob für Pageviews, Löschkonzept und der
Widerruf der Art.-9-Einwilligung.
**Grundlage:** Ausschließlich der tatsächliche Code in `/home/mrjaws/monatsmenue` (Stand Commit `0a2beef` + Arbeitsstand).

> **Wichtig:** Dies ist ein KI-generierter Entwurf. Er ersetzt **keine juristische Prüfung**. Vor dem Livegang – spätestens vor dem Start der kostenpflichtigen Version – muss eine Anwältin/ein Anwalt für IT- und Verbraucherrecht die Texte prüfen. Die folgenden Abschnitte benennen die Stellen, die dabei zuerst anzusehen sind.

---

## 1. Welche Lücke geschlossen wurde

Die drei Seiten waren inhaltlich nicht auf dem Stand der Anwendung. Der Datenschutz beschrieb im Wesentlichen die Warteliste; Konto, Haushaltsdaten, Gesundheitsdaten, Tracking und lokale Speicherung fehlten oder waren ungenau. Die AGB bestanden aus einem Platzhalter-Satz. Das Impressum war formal ok, nannte aber den E-Mail-Versender nicht und enthielt einen toten Link auf die 2025 eingestellte EU-OS-Plattform.

| Seite | Vorher | Jetzt |
|---|---|---|
| `datenschutz` | ~2.700 Zeichen, im Kern Warteliste | 19 Abschnitte: Verantwortlicher, Hosting/Logfiles, Warteliste (DOI), Konto/Login/Reset, Haushalts- und Plandaten, Art. 9, Angehörige, Reichweitenmessung, Cookies/localStorage, Google Fonts, E-Mail-Versand, Empfänger, Drittland, Speicherdauer, Sicherheit, Rechte, Art. 22, Beschwerde, Änderungen |
| `agb` | ein Platzhalter-Satz | 14 Paragrafen inkl. Beta-Status, Preise (kostenlos), Konto, Gesundheitshinweise, Nutzungsrechte, Haftung, Kündigung, Änderungen, vollständige Widerrufsbelehrung + Muster-Widerrufsformular, Streitbeilegung |
| `impressum` | § 5 DDG, Hosting, toter ODR-Link | § 5 DDG, E-Mail als schneller Kontakt (ohne Telefonnummer), USt-ID, § 18 MStV, Hetzner **und** Strato, Verbraucherstreitbeilegung ohne toten Link, Haftung/Links, Urheberrecht |

Zusätzlich korrigiert:

- Die alte Fassung behauptete, es würden „keine IP-Adressen im Klartext“ gespeichert. Das gilt für das Pageview-Tracking, **nicht** für die Warteliste: `waitlist.confirmed_ip` wird im Klartext gespeichert (`backend/app/models/database.py:272`, gesetzt in `backend/app/routes/waitlist.py:98`). Jetzt getrennt und korrekt dargestellt.
- Die alte AGB versprach eine Kontolöschung „jederzeit“ – dafür existiert **kein Endpoint**. Jetzt als Löschung per E-Mail formuliert, was dem tatsächlichen Ablauf entspricht.
- Google Fonts werden dynamisch von Google geladen (`frontend/app/layout.tsx:60-66`) und übertragen die IP an Google. Das fehlte komplett und ist jetzt Abschnitt 10 – siehe Risiko 1.

---

## 2. Aus dem Code belegte Angaben

| Aussage in den Rechtstexten | Beleg |
|---|---|
| Verantwortlicher, Anschrift, E-Mail, USt-ID | `frontend/app/impressum/page.tsx` (Bestand), `frontend/app/datenschutz/page.tsx` |
| Konto: E-Mail, Anzeigename, Passwort-Hash | `backend/app/models/database.py:54-65` |
| Passwort: PBKDF2-HMAC-SHA256, 16-Byte-Salt, 100.000 Iterationen | `backend/app/core/auth.py:18-26` |
| Cookie `sprossa_token`, httpOnly, SameSite=Lax, 24 h | `backend/app/routes/auth.py:70-78`, `:94-102`; gelesen in `backend/app/core/dependencies.py:24-25` |
| Logout löscht das Cookie | `backend/app/routes/auth.py:189-197` |
| Passwort-Reset-Token, 1 Stunde gültig | `backend/app/routes/auth.py:141-143`, `:166` |
| Haushalt: Name, dietary_profile, `health_data_consent_at` | `backend/app/models/database.py:70-81` |
| Mitglieder: Name, Alter, Gewicht, Allergien, Ziele, Notizen | `backend/app/models/database.py:91-102` |
| Rezepte, Monats-/Wochenpläne, Mahlzeiten, Einkaufslisten | `backend/app/models/database.py:123-257` |
| Einwilligung Art. 9 wird beim Anlegen gesetzt | `backend/app/routes/households.py:33` |
| Widerruf wird nur als Zeitstempel im Profil vermerkt | `backend/app/routes/households.py:61-66` |
| Einwilligungs-Checkbox nur bei ausgewählten Allergien | `frontend/app/onboarding/page.tsx:553-585`, Übertragung `:197` |
| Migration der Einwilligungsspalte | `backend/alembic/versions/f6a7b8c9d0e1_add_health_data_consent.py` |
| Warteliste: E-Mail, Name, Haushaltsgröße, Quelle, UTM, Bestätigungsstatus, IP bei Bestätigung | `backend/app/models/database.py:262-275` |
| Double-Opt-in, Token 48 h, Abmeldung löscht den Eintrag | `backend/app/routes/waitlist.py:76-120` |
| Pageview: Pfad, Referrer, UTM, Gerät, `session_hash` | `backend/app/models/database.py:280-300`, `backend/app/routes/track.py:104-114` |
| `session_hash` = SHA-256 aus IP + User-Agent + Tagesdatum, auf 32 Zeichen gekürzt, IP wird nicht gespeichert | `backend/app/routes/track.py:82-86`, `:95-98` |
| `sessionStorage` `sprossa_pv` | `frontend/app/Tracker.tsx:22-23` |
| `localStorage` `grocery_checked_*` | `frontend/app/dashboard/grocery/page.tsx:123`, `:264` |
| Kein Client-Token-Speicher (nur httpOnly-Cookie) | `frontend/app/lib/auth.ts:1-5` |
| E-Mail-Versand über `smtp.strato.de` | `backend/app/core/config.py:24-29`, `backend/app/services/email.py:1` |
| Hosting Hetzner, Server in Deutschland | `docker-compose.yml`, `frontend/app/impressum/page.tsx` (Bestand), AVV laut Projektinhaber |
| Sicherungskopien 30 Tage | `scripts/backup_db.sh:17` (`RETENTION_DAYS=30`), `scripts/backup_pull_nas.sh:10` (`KEEP=30`) |
| Keine Werbe-Tracker, kein Analytics, kein Newsletter | Keine Treffer für `gtag`, `analytics`, `pixel`, `newsletter` in `frontend/app`, `backend/app`; nur Pageview-Tabelle |
| Keine Zahlungsabwicklung in der Beta | `backend/app/routes/family.py:863-880` sind Stubs; `stripe_customer_id` bleibt ungenutzt (`database.py:61`) |

Nicht belegt und daher **nicht** in die Texte geschrieben: eine konkrete Logfile-Aufbewahrungsfrist, eine Auftragsverarbeitung mit Strato, ein Datenschutzbeauftragter, eine Registrierungspflicht für Minderjährige.

---

## 3. Bewusste Abweichung: keine Telefonnummer im Impressum

§ 5 Abs. 1 Nr. 2 DDG verlangt Angaben, die eine **schnelle elektronische Kontaktaufnahme und unmittelbare Kommunikation** ermöglichen, einschließlich einer E-Mail-Adresse. Die Telefonnummer ist nach überwiegender Auffassung nicht zwingend, wenn die E-Mail-Adresse schnelle Kommunikation ermöglicht.

Der Projektinhaber hat entschieden, **keine Telefonnummer** anzugeben (reine Online-Präsenz, Kontakt per E-Mail genügt). Das ist die bewusst gewählte, weniger konservative Auslegung. Das Impressum benennt die E-Mail-Adresse ausdrücklich als Weg der schnellen elektronischen Kontaktaufnahme und nennt eine Antwortzeit, damit die Argumentation tragfähig ist. Restrisiko: Ein Wettbewerber oder eine Verbraucherzentrale könnte die Angabe vermissen; das Risiko ist gering, aber nicht null (siehe Abschnitt 6, Punkt 6).

---

## 4. Vom Projektinhaber noch zu bestätigen

1. **Rechtsform und Inhaberschaft:** Ist „The Oaktree“ ein eingetragenes Einzelunternehmen, eine GbR oder nur eine Marke? Gehört der Betrieb Sebastian Westhoff persönlich? Ggf. Handelsregister/Partnerschaftsregister und Register-Nr. ergänzen.
2. **Serverstandort:** Falkenstein (Sachsen) – bitte anhand des Hetzner-Vertrags bestätigen; falls Nürnberg oder ein anderer Standort, Text anpassen.
3. **AVV Strato:** Besteht ein Auftragsverarbeitungsvertrag für den E-Mail-Versand? Der Text behauptet ihn derzeit.
4. **AVV Hetzner:** laut Auftrag vorhanden – Datum/Abschluss bitte intern dokumentieren.
5. **Datenschutzbeauftragter:** Der Text behauptet keine Bestellung, sondern verweist auf die gesetzliche Pflicht. Bitte prüfen, ob die Schwellenwerte des Art. 37 DSGVO / § 38 BDSG erreicht werden (bei weniger als 20 Personen, die ständig mit automatisierter Verarbeitung befasst sind, in der Regel nicht). Falls doch: Kontaktdaten ergänzen.
6. **Logfile-Aufbewahrung:** Wie lange werden Caddy-/Container-Logs tatsächlich aufbewahrt? Der Text nennt bewusst keine Zahl; für die DSFA-/Rechenschaftsakte sollte eine Frist festgelegt und im Text ergänzt werden.
7. **Warteliste nach Beta-Ende:** Der Text nennt „spätestens 12 Monate nach Ende der Beta-Phase“. Enddatum und Löschroutine bestätigen.
8. **Beta-Dauer und Preismodell:** Wann endet die Beta, ist ein Abo geplant, welcher Zahlungsdienstleister? Der Datenschutztext kündigt Stripe als „vorgesehen“ an.
9. **Mindestalter:** Die AGB verlangen 18 Jahre, die Registrierung prüft das nicht. Entweder Altersabfrage einbauen oder die Klausel anpassen.
10. **Redaktionelle Inhalte:** Sind Rezepte redaktionell aufbereitet? Dann ist die Angabe nach § 18 Abs. 2 MStV korrekt und sollte um die Anschrift ergänzt bleiben.

---

## 5. Technische Lücken mit Rechtsbezug (vor Go-live zu beheben)

Diese Punkte sind **keine** Textfehler, sondern Abweichungen zwischen Text und System. Sie sind nach Risiko sortiert.

1. **Google Fonts werden dynamisch geladen** (`frontend/app/layout.tsx:60-66`). Dabei geht die IP-Adresse an Google. Das LG München I hat das 2022 ohne Einwilligung als rechtswidrig eingestuft. Der Datenschutztext offenbart es jetzt, was besser als Schweigen ist, aber die Rechtswidrigkeit nicht heilt. **Empfehlung:** Schriften lokal ausliefern (`next/font/local` oder Dateien in `public/fonts`), dann Abschnitt 10 streichen.
2. **Kein Löschjob für Pageview-Daten.** Der Text verspricht 90 Tage; im Code existiert keine Aufräumroutine (`grep` nach `delete`/`retention` in `backend/app` ohne Treffer für `pageview`). Entweder Job implementieren oder die Frist anpassen.
3. **Kein Endpoint zur Kontolöschung.** AGB § 5 und Datenschutz Abschnitt 14 verweisen auf E-Mail-Löschung. Das ist rechtlich zulässig, aber es gibt keinen dokumentierten manuellen Prozess. Löschkonzept schriftlich festlegen (wer, wie, Frist, Backup).
4. **Widerruf der Art.-9-Einwilligung löscht die Daten nicht.** `households.py:61-66` setzt nur `health_data_consent_revoked_at` im JSON; die Allergien in `members.allergies` bleiben stehen. Der Text sagt „wir löschen die Angaben“ – das muss entweder im Code passieren oder der Text muss ehrlicher formuliert werden.
5. **JWT wird mit dem hartkodierten Default-Secret signiert.** `backend/app/core/auth.py:36` (`_SECRET_KEY = "change-me-in-production"`), `create_access_token`/`decode_access_token` nutzen diesen Default; `MM_SECRET_KEY` aus `.env.example` wird nicht verwendet. Damit sind Sitzungs-Token fälschbar – ein Verstoß gegen Art. 32 DSGVO und ein Widerspruch zu Abschnitt 15 der Datenschutzerklärung.
6. **Cookie mit `secure=False`** (`backend/app/routes/auth.py:74`, `:98`, `:193`) – das Sitzungs-Cookie würde auch über HTTP gesendet. In Produktion auf `True` stellen.
7. **Keine Zustimmung zu AGB/Datenschutz bei der Registrierung.** `frontend/app/register/page.tsx` enthält keine Checkbox und keinen Link. Damit ist die Einbeziehung der AGB angreifbar. Empfehlung: Pflicht-Checkbox mit Links auf `/agb` und `/datenschutz`, Zeitstempel speichern.
8. **Warteliste speichert die IP im Klartext** (`confirmed_ip`). Zweck ist nachvollziehbar (Missbrauchsschutz), aber Löschfrist und Rechtsgrundlage sollten im Verzeichnis der Verarbeitungstätigkeiten stehen.
9. **Reset-Token im Klartext in der Datenbank** (`users.reset_token`), 1 Stunde gültig. Akzeptabel, aber Hashing wäre besser.

---

## 6. Juristisch zu prüfen – die fünf riskantesten Punkte

1. **Google Fonts / Drittlandübermittlung.** Ohne lokale Auslieferung bleibt ein abmahnfähiger Punkt. Wenn die Schriften lokal liegen, entfällt der Abschnitt und das Risiko. Das ist die wirksamste Einzelmaßnahme.
2. **Gesundheitsdaten nach Art. 9 DSGVO.** Die Einwilligung wird nur abgefragt, wenn Allergien ausgewählt sind – gut. Aber: (a) der Widerruf löscht die Daten nicht, (b) Daten weiterer Haushaltsmitglieder werden ohne deren eigene Einwilligung gespeichert, (c) die Einwilligung ist nicht getrennt von der allgemeinen Registrierung dokumentiert. Das ist der Kern des Geschäftsmodells und braucht eine saubere Prüfung inkl. Datenschutz-Folgenabschätzung.
3. **Reichweitenmessung ohne Einwilligung.** Der tägliche Hash aus IP + User-Agent ist pseudonym, aber möglicherweise weiterhin personenbezogen. Die Argumentation „keine personenbezogenen Daten, daher kein Consent“ ist angreifbar; sie steht so auch im Code-Kommentar (`frontend/app/Tracker.tsx:11-13`). Zu prüfen: Reichweitenmessung auf Art. 6 Abs. 1 lit. f stützen, Speicherdauer verkürzen, keine Referrer-URLs mit personenbezogenen Bestandteilen speichern.
4. **Widerrufsbelehrung und kostenpflichtige Version.** Die Belehrung ist vollständig, aber die Pflichtangaben für digitale Inhalte (§ 356 Abs. 5 BGB, Button-Lösung, Preisangaben) greifen erst beim Bezahlmodell. Außerdem ist die Zustimmungsfiktion in AGB § 11 gegenüber Verbrauchern bei Preisänderungen regelmäßig unwirksam. Vor dem Paid-Launch neu bewerten.
5. **Haftung für Allergiefolgen.** Die Freizeichnung in AGB § 9 Abs. 3 und die Hinweise in § 6 sind notwendig, aber bei Personenschäden nicht belastbar einschränkbar. Zu prüfen ist außerdem, ob die Beta-Klausel „Datenverluste möglich“ ausreicht oder ob eine klarere Risikobelehrung nötig ist.

Zusätzlich prüfen: **Impressum ohne Telefonnummer** (§ 5 DDG, geringes Risiko, bewusste Entscheidung des Inhabers) und die **Datenschutzerklärung gegenüber Minderjährigen** (Kinderdaten im Haushaltsprofil).

---

## 7. Geänderte Dateien

- `frontend/app/datenschutz/page.tsx` – neu geschrieben, 19 Abschnitte
- `frontend/app/agb/page.tsx` – neu geschrieben, 14 Paragrafen + Widerrufsbelehrung + Musterformular
- `frontend/app/impressum/page.tsx` – überarbeitet, ohne Telefonnummer, mit Strato, ohne toten ODR-Link
- `docs/rechtsseiten-2026-11.md` – dieser Bericht

**Geprüft:** `npx tsc --noEmit` ohne Fehler; `LANDING_BUILD=1 npx next build` erfolgreich, alle drei Seiten statisch prerendert. Kein Deployment, kein Push.

---

## 8. Nachtrag 06.11.2026 — behobene technische Lücken

| Lücke aus Abschnitt 5 | Umsetzung |
|---|---|
| 1 · Google Fonts dynamisch | Fraunces und Nunito liegen als 14 woff2-Dateien unter `frontend/public/fonts`, eingebunden per `@font-face` in `globals.css`. Der `<link>` auf `fonts.googleapis.com` ist entfernt. Live geprüft: 0 Google-Requests im HTML. Datenschutz Abschnitt 10 beschreibt jetzt die lokale Auslieferung. |
| 2 · JWT mit Default-Secret | `core/auth.py` liest `MM_SECRET_KEY` aus der Umgebung; fehlt es, wird ein zufälliges Secret erzeugt und gewarnt. Kein weltweit bekanntes Secret mehr. |
| 5 · Cookie ohne `Secure` | Neues Setting `MM_COOKIE_SECURE` (Default `True`), gesetzt in `core/config.py`, verwendet an allen drei `set_cookie`-Stellen. Test-Instanz läuft über HTTP und setzt es in `docker-compose.test.yml` auf `false`. Live geprüft: `HttpOnly; SameSite=lax`, ohne `Secure` im Test. |
| 8 · Keine AGB-Zustimmung | Pflicht-Checkbox auf `/register` mit Links auf AGB und Datenschutz; `accepted_terms` im Request (ohne → 422); serverseitiger Zeitstempel `users.terms_accepted_at` (Migration `a1b2c3d4e5f6`). |

**Weiterhin offen:** Löschjob für Pageview-Daten (Abschnitt 5.2), schriftliches
Löschkonzept (5.3), Löschung der Allergien beim Widerruf nach Art. 9 (5.4),
Hashing des Reset-Tokens (5.9).

**Nicht durch Code behebbar:** die juristische Prüfung selbst sowie die zehn
Bestätigungen aus Abschnitt 4 (Rechtsform, Serverstandort, AVV Strato,
Logfile-Fristen, Mindestalter, Preismodell).
