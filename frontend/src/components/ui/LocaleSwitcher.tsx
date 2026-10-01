import { getLocale, getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { localeNames, locales } from "@/i18n/routing";

/**
 * Locale switcher. A server component — six links need no JavaScript, and
 * rendering them server-side means crawlers follow them.
 *
 * Each label is written in its own language, which is how a visitor finds
 * their language without reading English first.
 */
export async function LocaleSwitcher() {
  const current = await getLocale();
  const t = await getTranslations("common");

  return (
    <nav aria-label={t("language")} className="flex flex-wrap items-center gap-x-1 gap-y-2">
      <span className="me-3 text-xs text-text-mute">{t("language")}</span>
      {locales.map((locale) => {
        const isCurrent = locale === current;
        return (
          <Link
            key={locale}
            href="/"
            locale={locale}
            hrefLang={locale}
            aria-current={isCurrent ? "true" : undefined}
            className={[
              "rounded-sm px-2 py-1 text-sm no-underline transition-colors duration-(--ax-duration) ease-ax",
              isCurrent
                ? "bg-surface text-text"
                : "text-text-mute hover:bg-surface hover:text-text",
            ].join(" ")}
          >
            {localeNames[locale]}
          </Link>
        );
      })}
    </nav>
  );
}
