import "server-only";

/**
 * Environment access, validated once at module load.
 *
 * Server-only values are read from process.env directly and must never be
 * imported into a client component. Anything the browser needs carries the
 * NEXT_PUBLIC_ prefix (CLAUDE.md section 4: no secrets in code).
 */

function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(
      `Missing environment variable ${name}. Copy .env.example to .env.local and fill it in.`,
    );
  }
  return value;
}

/** Django REST API base, server-side. Includes the /api/v1 prefix. */
export const API_URL = required("API_URL", process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL);

/** Same API, for the one client-side call we allow: the contact form POST. */
export const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? API_URL;

/** Absolute public origin. Canonical URLs and hreflang are built from this. */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(
  /\/$/,
  "",
);

/** Shared secret the Django publish webhook presents to /api/revalidate. */
export const REVALIDATE_SECRET = process.env.REVALIDATE_SECRET ?? "";

export const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? "";

export const GA4_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID ?? "";
