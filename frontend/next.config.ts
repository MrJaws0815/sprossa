import { type NextConfig } from "next";

/**
 * Zwei Build-Modi:
 * 1. Standalone (Default) – Testinstanz/Dev-Container, schreibt nach `.next`.
 * 2. Landing-Build (`LANDING_BUILD=1`) – statische Produktions-Landingpage, schreibt in
 *    das separate `distDir` `.next-build`, damit der root-owned `.next` des laufenden
 *    Dev-Containers unangetastet bleibt. `scripts/build_landing.sh` setzt daraus die
 *    Landingpage zusammen, `scripts/deploy_landing.sh` schiebt sie nach Produktion.
 */
const isLandingBuild = process.env.LANDING_BUILD === "1";

const nextConfig: NextConfig = {
  output: "standalone",
  ...(isLandingBuild ? { distDir: ".next-build" } : {}),
  rewrites: async () => {
    const upstream = process.env.BACKEND_UPSTREAM_URL;
    if (upstream) {
      console.log(`[Sprossa-Rewrite] API-Upstream: ${upstream}`);
      return [
        { source: "/api/:path*", destination: `${upstream}/api/:path*` },
      ];
    }
    return [];
  },
};

export default nextConfig;