import { getTranslations } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import type { ServiceDetail, ServiceSummary } from "@/lib/api-types";
import { getPosts } from "@/lib/api";
import { caseCard, productCard, postCard } from "@/lib/cards";
import { SITE_URL } from "@/lib/env";
import { breadcrumbs } from "@/lib/metadata";
import { Container } from "@/components/ui/Container";
import { RichText } from "@/components/ui/RichText";
import { JsonLd } from "@/components/ui/JsonLd";
import { SectionNav } from "@/components/ui/SectionNav";
import { PageHero } from "./PageHero";
import { Section } from "./Section";
import { ContentGrid } from "./ContentGrid";
import { SpecificContent } from "./SpecificContent";
import { FaqList } from "./FaqList";
import { VideoSection } from "./VideoSection";
import { QuoteForm } from "./QuoteForm";
export async function ServicePage({
  service: s,
  services,
  locale,
}: {
  service: ServiceDetail;
  services: ServiceSummary[];
  locale: Locale;
}) {
  const t = await getTranslations("content");
  const nav = await getTranslations("nav");
  const posts = await getPosts(locale, { service: s.slug });
  const specific = Object.values(s.specific_content).some(
    (items) => items.length,
  );
  const sections = [
    ["overview", !!s.body],
    ["offerings", s.offerings.length],
    ["process", s.process_steps.length],
    ["specific", specific],
    ["videos", s.videos.length],
    ["products", s.products.length],
    ["industries", s.industries.length],
    ["tools", s.tools.length],
    ["work", s.case_studies.length],
    ["results", s.stats.length],
    ["testimonials", s.testimonials.length],
    ["posts", posts.results.length],
    ["faq", s.faqs.length],
    ["quote", true],
  ]
    .filter(([, show]) => show)
    .map(([id]) => ({
      id: String(id),
      label: t(String(id) === "specific" ? "specificTitle" : String(id)),
    }));
  return (
    <>
      <PageHero
        title={s.hero_headline || s.name}
        intro={s.hero_subline || s.intro}
        image={s.hero_image}
        quote
      />
      <Container className="ax-detail-layout">
        <SectionNav items={sections} label={t("onPage")} />
        <div className="min-w-0">
          {s.body && (
            <Section id="overview" title={t("overview")}>
              <RichText html={s.body} />
            </Section>
          )}
          {!!s.offerings.length && (
            <Section id="offerings" title={t("offerings")}>
              <div className="grid gap-8 sm:grid-cols-2">
                {s.offerings.map((item, i) => (
                  <div key={i}>
                    <h3 className="text-xl">{item.title}</h3>
                    <p className="mt-3 text-text-2">{item.description}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}
          {!!s.process_steps.length && (
            <Section id="process" title={t("process")}>
              <ol className="space-y-8">
                {s.process_steps.map((item, i) => (
                  <li key={i} className="flex gap-6">
                    <span
                      className="text-2xl text-text-mute"
                      aria-hidden="true"
                    >
                      {i + 1}
                    </span>
                    <div>
                      <h3 className="text-xl">{item.title}</h3>
                      <p className="mt-3 text-text-2">{item.description}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </Section>
          )}
          {specific && (
            <Section id="specific" title={t("specificTitle")}>
              <SpecificContent groups={s.specific_content} />
            </Section>
          )}
          {!!s.videos.length && (
            <Section id="videos" title={t("videos")}>
              <VideoSection videos={s.videos} locale={locale} />
            </Section>
          )}
          {!!s.products.length && (
            <Section id="products" title={t("products")}>
              <ContentGrid
                items={s.products.map(productCard)}
                prefix="/products"
              />
            </Section>
          )}
          {!!s.industries.length && (
            <Section id="industries" title={t("industries")}>
              <ul className="grid gap-6 sm:grid-cols-2">
                {s.industries.map((item) => (
                  <li key={item.slug}>
                    <h3 className="text-lg">{item.name}</h3>
                    <p className="mt-2 text-text-2">{item.description}</p>
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {!!s.tools.length && (
            <Section id="tools" title={t("tools")}>
              <ul className="flex flex-wrap gap-3">
                {s.tools.map((item) => (
                  <li
                    key={item.slug}
                    className="border border-border px-4 py-2"
                  >
                    {item.name}
                  </li>
                ))}
              </ul>
            </Section>
          )}
          {!!s.case_studies.length && (
            <Section id="work" title={t("work")}>
              <ContentGrid
                items={s.case_studies.map(caseCard)}
                prefix="/work"
              />
            </Section>
          )}
          {!!s.stats.length && (
            <Section id="results" title={t("results")}>
              <dl className="grid gap-8 sm:grid-cols-3">
                {s.stats.map((item, i) => (
                  <div key={i}>
                    <dt className="text-text-mute">{item.label}</dt>
                    <dd className="mt-3 text-3xl">
                      <bdi>
                        {item.value}
                        {item.unit}
                      </bdi>
                    </dd>
                  </div>
                ))}
              </dl>
            </Section>
          )}
          {!!s.testimonials.length && (
            <Section id="testimonials" title={t("testimonials")}>
              {s.testimonials.map((item, i) => (
                <figure key={i} className="mb-8 border-s-2 border-border ps-6">
                  <blockquote className="text-xl">{item.quote}</blockquote>
                  <figcaption className="mt-4 text-sm text-text-mute">
                    {[item.client_name, item.client_role, item.client_company]
                      .filter(Boolean)
                      .join(" · ")}
                  </figcaption>
                </figure>
              ))}
            </Section>
          )}
          {!!posts.results.length && (
            <Section id="posts" title={t("posts")}>
              <ContentGrid
                items={posts.results.slice(0, 3).map(postCard)}
                prefix="/blog"
              />
            </Section>
          )}
          {!!s.faqs.length && (
            <Section id="faq" title={t("faq")}>
              <FaqList items={s.faqs} />
              <JsonLd
                data={{
                  "@context": "https://schema.org",
                  "@type": "FAQPage",
                  mainEntity: s.faqs.map((f) => ({
                    "@type": "Question",
                    name: f.question,
                    acceptedAnswer: { "@type": "Answer", text: f.answer },
                  })),
                }}
              />
            </Section>
          )}
          <Section id="quote" title={t("quote")}>
            <QuoteForm services={services} service={s.slug} />
          </Section>
        </div>
      </Container>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Service",
          name: s.name,
          description: s.intro,
          url: `${SITE_URL}/${locale}/${s.slug}`,
          provider: { "@id": `${SITE_URL}/#organization` },
        }}
      />
      <JsonLd
        data={breadcrumbs(locale, [
          { name: nav("home"), path: "" },
          { name: s.name, path: `/${s.slug}` },
        ])}
      />
    </>
  );
}
