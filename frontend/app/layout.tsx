import type { Metadata } from "next";
import "./globals.css";
import SprossaHeader from "./Header";

export const metadata: Metadata = {
  title: "Sprossa – Familien-Monatsplaner",
  description:
    "Sprossa pflanzt euren ganzen Monat: Rezepte für jeden Tag, Cook-Once-Eat-Twice-Strategie, smarte Einkaufsliste. Für Familien.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      {/* Fonts: Nunito (UI/Body) + Fraunces (Displays) – preconnect für schnellen Load */}
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Fraunces:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <SprossaHeader />
        {children}
      </body>
    </html>
  );
}