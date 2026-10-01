import type { Metadata } from "next";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { directionOf, localeTags, locales, routing, type Locale } from "@/i18n/routing";
import { fontsForLocale } from "@/styles/fonts";
import { SITE_URL } from "@/lib/env";

import "@/styles/globals.css";

/**
 * Every locale is generated at build time, so all six are static HTML.
 */
export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  const t = await getTranslations({ locale, namespace: "common" });

  return {
    metadataBase: new URL(SITE_URL),
    title: {
      default: `${t("brand")} — ${t("tagline")}`,
      template: `%s — ${t("brand")}`,
    },
    // Full per-route metadata, hreflang alternates and JSON-LD land in
    // Phase 7. This is the sitewide default only.
    openGraph: {
      siteName: t("brand"),
      locale: localeTags[locale as Locale],
      type: "website",
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  // Required for static rendering of a localised route.
  setRequestLocale(locale);

  const dir = directionOf(locale);
  const { className, localeFontVar } = fontsForLocale(locale);

  return (
    <html
      lang={localeTags[locale]}
      dir={dir}
      className={className}
      // Drives the --ax-font-locale fallback, so Arabic and Chinese prose
      // never renders in a Latin face (CLAUDE.md section 7).
      style={{ "--ax-font-locale": localeFontVar } as React.CSSProperties}
      suppressHydrationWarning
    >
      <body>
        <NextIntlClientProvider>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
