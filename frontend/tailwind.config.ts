import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "sprossa-green": "#3A7D44",
        "sprossa-dark": "#2C5F34",
        "sprossa-sage": "#EDF3E8",
        "sprossa-cream": "#FAF6EF",
        "sprossa-terracotta": "#D96B4A",
        "sprossa-amber": "#E6A23C",
        "sprossa-ink": "#26302B",
        "sprossa-muted": "#68736C",
        "sprossa-error": "#C0392B",
      },
      fontFamily: {
        body: ["Nunito", "Segoe UI", "system-ui", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;