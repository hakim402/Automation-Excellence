/*
 * next/font self-hosts the Latin families. Arabic and Chinese use vendored
 * font files and locale-specific stylesheets in public/fonts.
 *
 * Per CLAUDE.md section 7 a locale loads only the subsets it needs: the
 * Arabic and Chinese stylesheets retain Unicode ranges and fallback metrics;
 * Latin visitors do not download their CSS or font files.
 */

import { Archivo, IBM_Plex_Mono, Inter } from "next/font/google";

/** Display — industrial grotesque. Headlines, service names, numbers. */
export const archivo = Archivo({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-archivo",
  display: "swap",
});

/** Body — all running text and UI. */
export const inter = Inter({
  subsets: ["latin"],
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
  preload: false,
});

/** Non-Latin font CSS is linked only for its locale in the server layout. */
export function fontsForLocale(locale: string): {
  className: string;
  localeFontVar: string;
} {
  const latin = `${archivo.variable} ${inter.variable} ${plexMono.variable}`;
  return {
    className: latin,
    localeFontVar:
      locale === "ar"
        ? "var(--font-plex-arabic)"
        : locale === "zh"
          ? "var(--font-noto-sc)"
          : "ui-sans-serif",
  };
}
