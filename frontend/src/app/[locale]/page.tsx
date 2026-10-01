import { getTranslations, setRequestLocale } from "next-intl/server";

import { LocaleSwitcher } from "@/components/ui/LocaleSwitcher";
import { directionOf, type Locale } from "@/i18n/routing";

/**
 * Phase 0 placeholder.
 *
 * Its job is to prove the scaffold: six routed locales, correct `dir`, the
 * Deep Harbor tokens, and the right font stack per locale. It is replaced by
 * the real home page in Phase 6.
 *
 * Written with logical properties only (ms/me, ps/pe, text-start, border-s),
 * so the Arabic layout mirrors without a single RTL override.
 */
export default async function ScaffoldPage({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations("scaffold");
  const common = await getTranslations("common");
  const dir = directionOf(locale);

  const checks: { label: string; value: string; mono?: boolean }[] = [
    { label: t("checks.locales"), value: "en · es · fr · de · zh · ar", mono: true },
    { label: t("checks.direction"), value: dir === "rtl" ? t("directionRtl") : t("directionLtr") },
    { label: t("checks.tokens"), value: "tokens.css", mono: true },
    { label: t("checks.fonts"), value: fontStackLabel(locale), mono: true },
    { label: t("checks.api"), value: t("apiPending") },
  ];

  return (
    <main className="mx-auto w-full max-w-(--container-ax) px-gutter py-section-lg">
      <header className="flex flex-col gap-6">
        <div className="flex items-center gap-3">
          {/* The single amber element on this page. Amber stays rare. */}
          <span
            aria-hidden="true"
            className="size-1.5 shrink-0 rounded-full bg-ax-amber"
          />
          <span className="ax-mono text-2xs text-ax-slate">{t("status")}</span>
        </div>

        <div className="flex flex-col gap-2">
          <p className="font-display text-2xl font-semibold tracking-tight text-ax-paper">
            {common("brand")}
          </p>
          <p className="text-base text-ax-muted">{common("tagline")}</p>
        </div>
      </header>

      <div className="mt-section-md flex flex-col gap-5 border-s-2 border-ax-cyan ps-6">
        <h1 className="max-w-(--ax-measure-narrow) text-4xl text-ax-paper">{t("heading")}</h1>
        <p className="max-w-(--ax-measure) text-lg leading-(--ax-leading-relaxed) text-ax-muted">
          {t("intro")}
        </p>
      </div>

      <section className="mt-section-md rounded-lg border border-ax-border bg-ax-surface">
        <ul className="m-0 list-none p-0">
          {checks.map((check, index) => (
            <li
              key={check.label}
              className={[
                "flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 px-5 py-4",
                index > 0 ? "border-t border-ax-border" : "",
              ].join(" ")}
            >
              <span className="text-sm text-ax-muted">{check.label}</span>
              <span
                className={[
                  "text-start text-sm text-ax-paper",
                  check.mono ? "ax-mono text-xs" : "",
                ].join(" ")}
              >
                {check.value}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <footer className="mt-section-md border-t border-ax-border pt-8">
        <LocaleSwitcher />
      </footer>
    </main>
  );
}

/** Names the faces actually loaded for this locale, so substitution is visible. */
function fontStackLabel(locale: Locale): string {
  if (locale === "ar") return "Archivo · Inter · Plex Sans Arabic";
  if (locale === "zh") return "Archivo · Inter · Noto Sans SC";
  return "Archivo · Inter · Plex Mono";
}
