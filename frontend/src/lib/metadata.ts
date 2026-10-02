import "server-only";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { locales, localeTags, type Locale } from "@/i18n/routing";
import { SITE_URL } from "./env";
export async function shellMetadata(locale: Locale, route = "home"): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "nav" });
  const shell = await getTranslations({ locale, namespace: "shell" });
  const path = route === "home" ? "" : `/${route}`;
  const url = `${SITE_URL}/${locale}${path}`;
  return {
    title: { absolute: `${t(route)} — Automex` }, description: shell("description"), robots: { index: false, follow: true },
    alternates: { canonical: url, languages: { ...Object.fromEntries(locales.map(code => [localeTags[code], `${SITE_URL}/${code}${path}`])), "x-default": `${SITE_URL}/en${path}` } },
    openGraph: { title: `${t(route)} — Automex`, description: shell("description"), url, siteName: "Automex", locale: localeTags[locale], type: "website" },
  };
}
