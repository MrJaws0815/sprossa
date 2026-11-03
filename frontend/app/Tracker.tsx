"use client";

/**
 * Sprossa – Traffic-Tracking für die Landingpage.
 *
 * Schickt beim Seitenaufruf einen Pageview an /api/v1/track/pageview.
 * Erfasst UTM-Parameter aus der URL, den Referrer und die Geräteklasse.
 * Kein Cookie, keine IP-Speicherung, kein Fingerprinting –
 * der Server bildet einen täglichen Hash für die Besucherzählung.
 *
 * Datenschutz: DSGVO-konform ohne Consent-Banner, weil keine
 * personenbezogenen Daten gespeichert werden (Art. 6 Abs. 1 lit. f
 * berechtigtes Interesse an Reichweitenmessung; Daten minimiert).
 */

import { useEffect } from "react";

export default function Tracker() {
  useEffect(() => {
    // Nur einmal pro Session im selben Tab senden (sessionStorage, kein Cookie).
    try {
      if (sessionStorage.getItem("sprossa_pv")) return;
      sessionStorage.setItem("sprossa_pv", "1");
    } catch {
      // sessionStorage gesperrt (Private Mode) – dann trotzdem senden.
    }

    const params = new URLSearchParams(window.location.search);

    const device = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)
      ? "mobile"
      : "desktop";

    const payload = {
      path: window.location.pathname,
      referrer: document.referrer || null,
      utm_source: params.get("utm_source"),
      utm_medium: params.get("utm_medium"),
      utm_campaign: params.get("utm_campaign"),
      utm_content: params.get("utm_content"),
      device,
    };

    // Beacon ist die zuverlässigste Methode (feuert auch beim Wegklicken),
    // Fallback auf fetch für ältere Browser.
    const url = "/api/v1/track/pageview";
    const body = JSON.stringify(payload);

    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
    } else {
      fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(() => {});
    }
  }, []);

  return null;
}
