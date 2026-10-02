import "server-only";
import type { Metadata } from "next";
import { getSiteSettings } from "./api";
import { openGraphLocales, alternateOpenGraphLocales } from "./seo";
import { locales, localeTags, type Locale } from "@/i18n/routing";
import { SITE_URL } from "./env";
import type { SEO, SiteSettings } from "./api-types";
export async function pageMetadata(
  locale: Locale,
  path: string,
  title: string,
  description: string,
  seo?: Partial<SEO>,
): Promise<Metadata> {
  const site = await getSiteSettings(locale);
  const image =
    seo?.og_image || site?.default_og_image || `${SITE_URL}/og-default.png`;
  const summary =
    seo?.meta_description ||
    description ||
    site?.default_meta_description ||
    title;
  const url = `${SITE_URL}/${locale}${path}`;
  const pageTitle = seo?.meta_title || title;
  return {
    title: {
      absolute: pageTitle === "Automex" ? pageTitle : `${pageTitle} — Automex`,
    },
    description: summary,
    robots: { index: !seo?.noindex, follow: true },
    alternates: {
      canonical: url,
      languages: {
        ...Object.fromEntries(
          locales.map((code) => [
            localeTags[code],
            `${SITE_URL}/${code}${path}`,
          ]),
        ),
        "x-default": `${SITE_URL}/en${path}`,
      },
    },
    twitter: {
      card: "summary_large_image",
      title: pageTitle,
      description: summary,
      images: [image],
    },
    icons: { icon: site?.favicon || `${SITE_URL}/favicon.png` },
    openGraph: {
      title: seo?.meta_title || title,
      description: summary,
      url,
      siteName: "Automex",
      locale: openGraphLocales[locale],
      alternateLocale: alternateOpenGraphLocales(locale),
      type: "website",
      images: [{ url: image, alt: pageTitle }],
    },
  };
}
export function breadcrumbs(
  locale: Locale,
  items: { name: string; path: string }[],
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: `${SITE_URL}/${locale}${item.path}`,
    })),
  };
}
export function organization(site: SiteSettings) {
  return {
    "@context": "https://schema.org",
    "@type": ["Organization", "LocalBusiness"],
    "@id": `${SITE_URL}/#organization`,
    name: site.company_name,
    url: site.domain || SITE_URL,
    ...(site.logo && { logo: site.logo }),
    ...(site.email && { email: site.email }),
    ...(site.phone_us && { telephone: site.phone_us }),
    address: {
      "@type": "PostalAddress",
      streetAddress: [site.address_line_1, site.address_line_2]
        .filter(Boolean)
        .join(", "),
      addressLocality: site.city,
      addressRegion: site.state,
      postalCode: site.postal_code,
      addressCountry: site.country,
    },
    ...(site.service_area && { areaServed: site.service_area }),
    sameAs: [
      site.linkedin_url,
      site.github_url,
      site.x_url,
      site.instagram_url,
      site.facebook_url,
      site.youtube_url,
    ].filter(Boolean),
  };
}
