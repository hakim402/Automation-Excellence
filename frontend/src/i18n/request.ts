import { hasLocale } from "next-intl";
import { getRequestConfig } from "next-intl/server";

import { deepMerge } from "./merge";
import { defaultLocale, routing } from "./routing";

/**
 * Per-request i18n config. `messages/*.json` holds interface strings only —
 * nav labels, buttons, form fields, errors. Page *content* comes from the
 * Django API (CLAUDE.md section 6).
 */
export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested) ? requested : defaultLocale;

  // English underneath every locale: a UI string that has not been translated
  // yet degrades to English rather than rendering blank (CLAUDE.md section 4).
  const fallback = (await import(`../../messages/${defaultLocale}.json`)).default;
  const messages =
    locale === defaultLocale
      ? fallback
      : deepMerge(fallback, (await import(`../../messages/${locale}.json`)).default);

  return {
    locale,
    messages,
    timeZone: "America/Los_Angeles",
    onError(error) {
      if (process.env.NODE_ENV === "development") {
        console.warn(`[i18n:${locale}] ${error.message}`);
      }
    },
    getMessageFallback({ key }) {
      return key;
    },
  };
});
