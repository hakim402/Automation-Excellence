"use client";
import { useLocale, useTranslations } from "next-intl";
import { useTransition } from "react";
import { usePathname, useRouter } from "@/i18n/navigation";
import { localeNames, locales, type Locale } from "@/i18n/routing";

export function LocaleSwitcher() {
  const current = useLocale();
  const t = useTranslations("common");
  const pathname = usePathname();
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <label className="flex items-center gap-2 text-sm text-text-2">
      <span className="sr-only">{t("language")}</span>
      <select value={current} disabled={pending} className="min-h-11 max-w-36 rounded-sm border border-border bg-surface px-3 text-text" onChange={(event) => {
        const locale = event.target.value as Locale;
        startTransition(() => router.replace(`${pathname}${window.location.search}${window.location.hash}`, { locale, scroll: false }));
      }}>
        {locales.map((locale) => <option key={locale} value={locale} lang={locale}>{localeNames[locale]}</option>)}
      </select>
    </label>
  );
}
