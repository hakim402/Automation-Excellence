import type { MetadataRoute } from "next";
import type { SitemapEntry } from "./api-types";
import { localeTags, locales, type Locale } from "@/i18n/routing";

/** Use the public frontend origin even when the API is served on another host. */
export function sitemapEntries(
  entries: SitemapEntry[],
  origin: string,
): MetadataRoute.Sitemap {
  const publicUrl = (value: string) =>
    new URL(new URL(value).pathname, origin).href;
  return entries.map((entry) => ({
    url: publicUrl(entry.url),
    ...(entry.lastmod && { lastModified: entry.lastmod }),
    alternates: {
      languages: Object.fromEntries(
        Object.entries(entry.alternates).map(([lang, url]) => [
          lang === "x-default" ? lang : localeTags[lang as Locale] || lang,
          publicUrl(url),
        ]),
      ),
    },
  }));
}
export function validMeasurementId(value: string) {
  return /^G-[A-Z0-9]{6,20}$/.test(value);
}
export function analyticsPage(origin: string, pathname: string) {
  // Query strings and fragments can contain personal information; never send them.
  const url = new URL(pathname, origin);
  return { page_location: url.origin + url.pathname, page_referrer: "" };
}
export const openGraphLocales: Record<Locale, string> = {
  en: "en_US",
  es: "es_ES",
  fr: "fr_FR",
  de: "de_DE",
  zh: "zh_CN",
  ar: "ar_AR",
};
export const alternateOpenGraphLocales = (locale: Locale) =>
  locales
    .filter((code) => code !== locale)
    .map((code) => openGraphLocales[code]);
