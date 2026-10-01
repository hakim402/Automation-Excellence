/**
 * The only place the frontend talks to Django.
 *
 * No component file may fetch the backend directly (CLAUDE.md section 6).
 * Everything here runs on the server — during the static build or an ISR
 * revalidation — so page content is in the HTML before any JavaScript runs.
 *
 * Endpoint wrappers are added in Phase 4/5 once the API exists. This module
 * currently provides the transport those wrappers will share.
 */

import { API_URL } from "./env";
import type { Locale } from "@/i18n/routing";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly path: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type FetchOptions = {
  /** Locale passed to Django as ?lang=. Invalid or missing resolves to en. */
  locale?: Locale;
  /** Extra query parameters. Undefined and empty values are dropped. */
  query?: Record<string, string | number | boolean | undefined>;
  /** ISR window in seconds. Publishing triggers on-demand revalidation too. */
  revalidate?: number;
  /** Cache tags, so the publish webhook can invalidate precisely. */
  tags?: string[];
};

const DEFAULT_REVALIDATE = 3600;

function buildUrl(path: string, { locale, query }: FetchOptions): string {
  const url = new URL(`${API_URL.replace(/\/$/, "")}/${path.replace(/^\//, "")}`);

  if (locale) {
    url.searchParams.set("lang", locale);
  }

  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

/**
 * GET a JSON payload from the API. Throws ApiError on a non-2xx response —
 * callers decide between notFound() and a degraded render.
 */
export async function apiGet<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const url = buildUrl(path, options);

  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    next: {
      revalidate: options.revalidate ?? DEFAULT_REVALIDATE,
      tags: options.tags,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, path, `GET ${path} returned ${response.status}`);
  }

  return (await response.json()) as T;
}

/**
 * As apiGet, but a 404 resolves to null instead of throwing. For routes that
 * render notFound() when content is unpublished or missing.
 */
export async function apiGetOptional<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T | null> {
  try {
    return await apiGet<T>(path, options);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}
