import { getTranslations } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import type { CaseDetail } from "@/lib/api-types";
import { Link } from "@/i18n/navigation";
import { breadcrumbs } from "@/lib/metadata";
import { JsonLd } from "@/components/ui/JsonLd";
import { Container } from "@/components/ui/Container";
import { RichText } from "@/components/ui/RichText";
import { buttonClass } from "@/components/ui/Button";
import { Section } from "./Section";
import { PageHero } from "./PageHero";
import { Gallery } from "./Gallery";
import { VideoSection } from "./VideoSection";
export async function CasePage({
  item,
  locale,
}: {
  item: CaseDetail;
  locale: Locale;
}) {
  const t = await getTranslations("content");
  const nav = await getTranslations("nav");
  return (
    <>
      <PageHero
        title={item.title}
        intro={item.client_name}
        image={item.cover_image}
      />
      <Container className="max-w-5xl pb-section-lg">
        <div className="mb-10 flex flex-wrap gap-4 text-text-mute">
          {item.service && (
            <Link href={`/${item.service.slug}`}>{item.service.name}</Link>
          )}
          {item.industry && <span>{item.industry.name}</span>}
          {item.country && <span>{item.country}</span>}
        </div>
        {(["challenge", "solution", "outcome"] as const).map(
          (key) =>
            item[key] && (
              <Section key={key} id={key} title={t(key)}>
                <RichText html={item[key]} />
              </Section>
            ),
        )}
        {!!item.metrics.length && (
          <Section id="results" title={t("results")}>
            <dl className="grid gap-8 sm:grid-cols-3">
              {item.metrics.map((metric, i) => (
                <div key={i}>
                  <dt className="text-text-mute">{metric.label}</dt>
                  <dd className="mt-4 text-3xl">
                    <bdi>
                      {metric.value}
                      {metric.unit}
                    </bdi>
                  </dd>
                </div>
              ))}
            </dl>
          </Section>
        )}
        {!!item.gallery.length && (
          <Section id="gallery" title={t("gallery")}>
            <Gallery items={item.gallery} title={item.title} />
          </Section>
        )}
        {!!item.videos.length && (
          <Section id="videos" title={t("videos")}>
            <VideoSection videos={item.videos} locale={locale} />
          </Section>
        )}
        {!!item.tech_stack.length && (
          <Section id="tools" title={t("tools")}>
            <p>{item.tech_stack.map((tool) => tool.name).join(" · ")}</p>
          </Section>
        )}
        <div className="mt-8 flex flex-wrap gap-5">
          <Link href="/contact" className={buttonClass()}>
            {t("quote")}
          </Link>
          {item.project_url && (
            <a
              href={item.project_url}
              rel="noopener noreferrer"
              className={buttonClass("secondary")}
            >
              {t("visit")}
            </a>
          )}
        </div>
        <JsonLd
          data={breadcrumbs(locale, [
            { name: nav("home"), path: "" },
            { name: nav("work"), path: "/work" },
            { name: item.title, path: `/work/${item.slug}` },
          ])}
        />
      </Container>
    </>
  );
}
