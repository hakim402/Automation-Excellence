import path from "path";

import createNextIntlPlugin from "next-intl/plugin";
import type { NextConfig } from "next";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

/** Backend media host, for next/image remotePatterns. */
const mediaUrl = new URL(process.env.NEXT_PUBLIC_MEDIA_URL ?? "http://127.0.0.1:8000/media/");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Keep a running dev server from overwriting a production build.
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  poweredByHeader: false,
  // Bound build-time API traffic for the single-VPS Django deployment.
  experimental: { cpus: 2, staticGenerationMaxConcurrency: 2 },

  // Pin file tracing to this project. Without it Next walks up and finds an
  // unrelated package-lock.json outside the repo, and warns on every build.
  outputFileTracingRoot: path.join(import.meta.dirname, "."),

  images: {
    // Images are served from Django's /media. Never a wildcard host.
    remotePatterns: [
      {
        protocol: mediaUrl.protocol.replace(":", "") as "http" | "https",
        hostname: mediaUrl.hostname,
        port: mediaUrl.port,
        pathname: "/media/**",
      },
    ],
    formats: ["image/avif", "image/webp"],
  },

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default withNextIntl(nextConfig);
