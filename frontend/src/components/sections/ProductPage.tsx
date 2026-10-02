import { getTranslations } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import type { ProductDetail, ServiceSummary } from "@/lib/api-types";
import { getCases, getService } from "@/lib/api";
import { caseCard } from "@/lib/cards";
import { breadcrumbs } from "@/lib/metadata";
import { Container } from "@/components/ui/Container";
import { JsonLd } from "@/components/ui/JsonLd";
import { RichText } from "@/components/ui/RichText";
import { SectionNav } from "@/components/ui/SectionNav";
import { Link } from "@/i18n/navigation";
import { Section } from "./Section";
import { PageHero } from "./PageHero";
import { Gallery } from "./Gallery";
import { VideoSection } from "./VideoSection";
import { ContentGrid } from "./ContentGrid";
import { FaqList } from "./FaqList";
import { QuoteForm } from "./QuoteForm";
export async function ProductPage({
  product: p,
  services,
  locale,
}: {
  product: ProductDetail;
  services: ServiceSummary[];
  locale: Locale;
}) {
  const t = await getTranslations("content");
  const nav = await getTranslations("nav");
  const related = await Promise.all(
    p.services.map(async (service) => ({
      service: await getService(locale, service.slug),
      cases: await getCases(locale, { service: service.slug }),
    })),
  );
  const cases = [
    ...new Map(
      related.flatMap((r) => r.cases.results).map((c) => [c.slug, c]),
    ).values(),
  ].slice(0, 3);
  const faqs = [
    ...new Map(
      related.flatMap((r) => r.service?.faqs || []).map((f) => [f.question, f]),
    ).values(),
  ];
  const items = [
    ["overview", true],
    ["features", p.features.length],
    ["gallery", p.gallery.length],
    ["videos", p.videos.length],
    ["tools", p.tech_stack.length],
    ["relatedServices", p.services.length],
    ["work", cases.length],
    ["faq", faqs.length],
    ["quote", true],
  ]
    .filter(([, show]) => show)
    .map(([id]) => ({ id: String(id), label: t(String(id)) }));
  return (
    <>
      <PageHero
        title={p.name}
        intro={p.tagline || p.summary}
        image={p.cover_image}
        quote
      />
      <Container className="ax-detail-layout">
        <SectionNav items={items} label={t("onPage")} />
        <div className="min-w-0">
          <Section id="overview" title={t("overview")}>
            <p className="mb-6 text-text-2">{p.summary}</p>
            <RichText html={p.body} />
            <p className="mt-6 text-sm text-text-mute">
              {t(`categories.${p.category}`)} · {t(`delivery.${p.delivery}`)}
            </p>
            <div className="mt-6 flex gap-5">
              {p.demo_url && (
                <a href={p.demo_url} rel="noopener noreferrer">
                  {t("demo")}
                </a>
              )}
              {p.docs_url && (
                <a href={p.docs_url} rel="noopener noreferrer">
                  {t("documentation")}
                </a>
              )}
            </div>
          </Section>
          {!!p.features.length && (
            <Section id="features" title={t("features")}>
              <div className="grid gap-8 sm:grid-cols-2">
                {p.features.map((item, i) => (
                  <div key={i}>
                    <h3 className="text-xl">{item.title}</h3>
                    <p className="mt-3 text-text-2">{item.description}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}
          {!!p.gallery.length && (
            <Section id="gallery" title={t("gallery")}>
              <Gallery items={p.gallery} title={p.name} />
            </Section>
          )}
          {!!p.videos.length && (
            <Section id="videos" title={t("videos")}>
              <VideoSection videos={p.videos} locale={locale} />
            </Section>
          )}
          {!!p.tech_stack.length && (
            <Section id="tools" title={t("tools")}>
              <ul className="flex flex-wrap gap-3">
                {p.tech_stack.map((tool) => (
                  <li
                    key={tool.slug}
                    className="border border-border px-4 py-2"
                  >
                    {tool.name}
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {!!p.services.length && (
            <Section id="relatedServices" title={t("relatedServices")}>
              <ul className="space-y-4">
                {p.services.map((s) => (
                  <li key={s.slug}>
                    <Link href={`/${s.slug}`}>{s.name}</Link>
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {!!cases.length && (
            <Section id="work" title={t("work")}>
              <ContentGrid prefix="/work" items={cases.map(caseCard)} />
            </Section>
          )}
          {!!faqs.length && (
            <Section id="faq" title={t("serviceFaq")}>
              <FaqList items={faqs} />
              <JsonLd
                data={{
                  "@context": "https://schema.org",
                  "@type": "FAQPage",
                  mainEntity: faqs.map((f) => ({
                    "@type": "Question",
                    name: f.question,
                    acceptedAnswer: { "@type": "Answer", text: f.answer },
                  })),
                }}
              />
            </Section>
          )}
          <Section id="quote" title={t("requestDemo")}>
            <QuoteForm services={services} product={p.slug} />
          </Section>
        </div>
      </Container>
      <JsonLd
        data={breadcrumbs(locale, [
          { name: nav("home"), path: "" },
          { name: nav("products"), path: "/products" },
          { name: p.name, path: `/products/${p.slug}` },
        ])}
      />
    </>
  );
}
