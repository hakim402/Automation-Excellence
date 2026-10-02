/** Server-only content transport. Browser form writes are a separate Phase 6 boundary. */
import "server-only";
import { cache } from "react";
import type {
  Paginated,
  ProductSummary,
  ServiceSummary,
  SiteSettings,
  ServiceDetail,
  ProductDetail,
  CaseSummary,
  CaseDetail,
  PostSummary,
  PostDetail,
  Category,
  TeamMember,
  HomeContent,
  SitemapEntry,
} from "./api-types";

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

const DEFAULT_REVALIDATE = 300;

function buildUrl(path: string, { locale, query }: FetchOptions): string {
  if (!/^\/[a-z0-9][a-z0-9/_-]*\/$/.test(path)) {
    throw new Error(
      "API paths must be relative endpoint paths with a trailing slash.",
    );
  }
  const url = new URL(
    `${API_URL.replace(/\/$/, "")}/${path.replace(/^\//, "")}`,
  );

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
export async function apiGet<T>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const url = buildUrl(path, options);

  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(10_000),
    next: {
      revalidate: options.revalidate ?? DEFAULT_REVALIDATE,
      tags: ["public-content", ...(options.tags ?? [])],
    },
  });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      path,
      `GET ${path} returned ${response.status}`,
    );
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

// React deduplicates layout/metadata reads within the same server render.
export const getSiteSettings = cache((locale: Locale) =>
  apiGetOptional<SiteSettings>("/site/settings/", {
    locale,
    tags: ["site-settings"],
  }),
);
export const getServices = cache((locale: Locale) =>
  apiGet<ServiceSummary[]>("/services/", { locale, tags: ["services"] }),
);
export function getProducts(
  locale: Locale,
  query: { category?: string; service?: string; page?: number } = {},
) {
  return apiGet<Paginated<ProductSummary>>("/products/", {
    locale,
    query,
    tags: ["products"],
  });
}

export const getHome = cache((locale: Locale) =>
  apiGet<HomeContent>("/home/", { locale }),
);
export const getService = cache((locale: Locale, slug: string) =>
  apiGetOptional<ServiceDetail>(`/services/${slug}/`, { locale }),
);
export const getProduct = cache((locale: Locale, slug: string) =>
  apiGetOptional<ProductDetail>(`/products/${slug}/`, { locale }),
);
export const getCase = cache((locale: Locale, slug: string) =>
  apiGetOptional<CaseDetail>(`/portfolio/case-studies/${slug}/`, { locale }),
);
export const getPost = cache((locale: Locale, slug: string) =>
  apiGetOptional<PostDetail>(`/blog/posts/${slug}/`, { locale }),
);
export function getCases(
  locale: Locale,
  query: { service?: string; industry?: string; page?: number } = {},
) {
  return apiGet<Paginated<CaseSummary>>("/portfolio/case-studies/", {
    locale,
    query,
  });
}
export function getPosts(
  locale: Locale,
  query: {
    category?: string;
    tag?: string;
    service?: string;
    page?: number;
  } = {},
) {
  return apiGet<Paginated<PostSummary>>("/blog/posts/", { locale, query });
}
export const getCategories = cache((locale: Locale) =>
  apiGet<Category[]>("/blog/categories/", { locale }),
);
export const getTeam = cache((locale: Locale) =>
  apiGet<TeamMember[]>("/team/", { locale }),
);
export const getSitemap = cache(() => apiGet<SitemapEntry[]>("/seo/sitemap/"));
export function validSlug(slug: string) {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug);
}
