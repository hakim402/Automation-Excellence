import { defineRouting } from "next-intl/routing";

/**
 * The six public locales, equal in status. English is the source of truth and
 * every other locale falls back to it (CLAUDE.md section 4).
 *
 * `localePrefix: "always"` keeps every URL explicit — /en/..., /ar/... — so
 * canonical URLs are self-referencing per locale and there is no un-prefixed
 * duplicate of the English site competing with itself in search results.
 *
 * Route slugs stay English in every locale by design (CLAUDE.md section 6):
 * /ar/cyber-security, never a transliterated path. hreflang does the SEO work.
 */
export const locales = ["en", "es", "fr", "de", "zh", "ar"] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "en";

/** Locales that render right-to-left. Mirrors RTL_LANGUAGES in Django. */
export const rtlLocales: readonly Locale[] = ["ar"];

/** Human-readable names, each written in its own language for the switcher. */
export const localeNames: Record<Locale, string> = {
  en: "English",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  zh: "中文",
  ar: "العربية",
};

/** BCP-47 tags for <html lang>, hreflang and Open Graph. */
export const localeTags: Record<Locale, string> = {
  en: "en",
  es: "es",
  fr: "fr",
  de: "de",
  zh: "zh-Hans",
  ar: "ar",
};

export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value);
}

export function directionOf(locale: Locale): "ltr" | "rtl" {
  return rtlLocales.includes(locale) ? "rtl" : "ltr";
}

export const routing = defineRouting({
  locales,
  defaultLocale,
  localePrefix: "always",
  // Locale comes from the URL only. No cookie or Accept-Language rewriting:
  // a crawler and a visitor must always see the same page at the same URL.
  localeDetection: false,
});
