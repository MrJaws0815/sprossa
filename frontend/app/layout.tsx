import type { Metadata } from "next";
import "./globals.css";
import SprossaHeader from "./Header";
import Tracker from "./Tracker";

const SITE_URL = "https://sprossa.de";
const DESCRIPTION =
  "Sprossa plant euren ganzen Monat: Rezepte für jeden Tag, Cook-Once-Eat-Twice-Strategie und eine Einkaufsliste, sortiert nach dem Weg durch den Supermarkt. Für Familien.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Sprossa – Familien-Monatsplaner",
    template: "%s · Sprossa",
  },
  description: DESCRIPTION,
  applicationName: "Sprossa",
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    locale: "de_DE",
    url: SITE_URL,
    siteName: "Sprossa",
    title: "Sprossa – Euer Monat. Einmal geplant.",
    description: DESCRIPTION,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Sprossa – Monatsplan für Familien mit Rezepten und Einkaufsliste",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Sprossa – Euer Monat. Einmal geplant.",
    description: DESCRIPTION,
    images: ["/og-image.png"],
  },
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Fraunces:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-sprossa-cream text-sprossa-ink">
        <Tracker />
        <SprossaHeader />
        {children}
      </body>
    </html>
  );
}
