import { ThemeProvider } from "@/components/ui/ThemeProvider";
import type { Metadata } from "next";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { directionOf, localeTags, locales, routing } from "@/i18n/routing";
import { fontsForLocale } from "@/styles/fonts";
import { SITE_URL } from "@/lib/env";

import { JsonLd } from "@/components/ui/JsonLd";
import { organization } from "@/lib/metadata";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { getSiteSettings, getServices } from "@/lib/api";
import "@/styles/globals.css";

/**
 * Every locale is generated at build time, so all six are static HTML.
 */
export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "Automex", template: "%s — Automex" },
};

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

  const [site, services, common] = await Promise.all([
    getSiteSettings(locale),
    getServices(locale),
    getTranslations("common"),
  ]);
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
        <ThemeProvider>
          <NextIntlClientProvider>
            <a href="#main-content" className="ax-skip-link">
              {common("skipToContent")}
            </a>
            <Header site={site} services={services} />
            <main id="main-content" tabIndex={-1} className="min-h-[24rem]">
              {children}
            </main>
            <Footer site={site} />
            {site && <JsonLd data={organization(site)} />}
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
