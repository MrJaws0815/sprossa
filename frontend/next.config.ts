import { type NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
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