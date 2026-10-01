/*
 * Font loading. next/font self-hosts each family and emits a CSS variable,
 * so there is no render-blocking request to Google and no layout shift.
 *
 * Per CLAUDE.md section 7 a locale loads only the subsets it needs: the
 * Arabic and Chinese faces declare their own subsets and are attached to
 * `<html>` only for `ar` and `zh`, so a Latin face never renders Arabic or
 * Chinese glyphs and Latin visitors never download a CJK file.
 */

import { Archivo, IBM_Plex_Mono, IBM_Plex_Sans_Arabic, Inter, Noto_Sans_SC } from "next/font/google";

/** Display — industrial grotesque. Headlines, service names, numbers. */
export const archivo = Archivo({
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700"],
  variable: "--font-archivo",
  display: "swap",
});

/** Body — all running text and UI. */
export const inter = Inter({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
  display: "swap",
});

/** Technical — real technical data only (tech stacks, metrics, code). */
export const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

/**
 * Arabic.
 *
 * `preload: false` is deliberate. next/font emits a <link rel="preload"> for
 * every declared family on every page of the route, and all six locales share
 * the one /[locale] route — so preloading here would make a German visitor
 * download the Arabic face. Without it the browser fetches this face only
 * when it meets a glyph in one of its unicode ranges, which happens only on
 * /ar. `display: swap` covers the one extra round trip.
 */
export const plexArabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "600"],
  variable: "--font-plex-arabic",
  display: "swap",
  preload: false,
});

/**
 * Chinese (Simplified). `preload: false` for the same reason as Arabic, and
 * it matters more here: Noto Sans SC is split across ~300 unicode ranges.
 *
 * `subsets: ["latin"]` is not a mistake and does not break Chinese. next/font
 * exposes only latin / latin-ext / vietnamese / cyrillic as subset names for
 * this family; the Han unicode ranges are emitted either way, so Chinese
 * renders in Noto Sans SC regardless of what is listed here. See the CSS
 * weight note in the Phase 0 report.
 */
export const notoSansSC = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-noto-sc",
  display: "swap",
  preload: false,
});

/**
 * The font classes and the locale fallback face for a given locale.
 *
 * `localeFontVar` is assigned to --ax-font-locale in the layout, which every
 * family in tokens.css falls through to. That is what keeps Arabic prose on
 * IBM Plex Sans Arabic rather than on Inter's fallback.
 */
export function fontsForLocale(locale: string): { className: string; localeFontVar: string } {
  const latin = `${archivo.variable} ${inter.variable} ${plexMono.variable}`;

  if (locale === "ar") {
    return {
      className: `${latin} ${plexArabic.variable}`,
      localeFontVar: "var(--font-plex-arabic)",
    };
  }

  if (locale === "zh") {
    return {
      className: `${latin} ${notoSansSC.variable}`,
      localeFontVar: "var(--font-noto-sc)",
    };
  }

  return { className: latin, localeFontVar: "ui-sans-serif" };
}
