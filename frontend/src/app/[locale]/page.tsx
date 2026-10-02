import { getTranslations, setRequestLocale } from "next-intl/server";
import { getHome, getServices, getSiteSettings } from "@/lib/api";
import { pageMetadata } from "@/lib/metadata";
import { caseCard, productCard, postCard } from "@/lib/cards";
import type { Locale } from "@/i18n/routing";
import { Link } from "@/i18n/navigation";
import { Container } from "@/components/ui/Container";
import { buttonClass } from "@/components/ui/Button";
import { Section } from "@/components/sections/Section";
import { ContentGrid } from "@/components/sections/ContentGrid";
import { SystemsReadout } from "@/components/sections/SystemsReadout";
import { QuoteForm } from "@/components/sections/QuoteForm";
export const revalidate = 300;
type Props = { params: Promise<{ locale: Locale }> };
export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const site = await getSiteSettings(locale);
  const nav = await getTranslations({ locale, namespace: "nav" });
  return pageMetadata(
    locale,
    "",
    site?.default_meta_title || site?.company_name || "Automex",
    site?.default_meta_description ||
      site?.about_short ||
      [
        "digital-marketing",
        "ai-automation",
        "custom-software",
        "web-development",
        "mobile-development",
        "cyber-security",
      ]
        .map((key) => nav(key))
        .join(" · "),
    { og_image: site?.default_og_image },
  );
}
export default async function Home({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [site, services, home, t] = await Promise.all([
    getSiteSettings(locale),
    getServices(locale),
    getHome(locale),
    getTranslations("content"),
  ]);
  return (
    <Container>
      <section className="grid items-center gap-12 py-section-lg lg:grid-cols-[1.3fr_1fr]">
        <div>
          {site?.city && (
            <p className="mb-6 text-sm text-text-mute">
              {[site.city, site.state].filter(Boolean).join(", ")}
              {site.service_area ? ` · ${site.service_area}` : ""}
            </p>
          )}
          <h1 className="max-w-3xl text-5xl">
            {site?.tagline || site?.company_name || "Automex"}
          </h1>
          {site?.about_short && (
            <p className="mt-6 max-w-xl text-lg text-text-2">
              {site.about_short}
            </p>
          )}
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="#quote" className={buttonClass()}>
              {t("quote")}
            </a>
            <Link href="/work" className={buttonClass("secondary")}>
              {t("seeWork")}
            </Link>
          </div>
        </div>
        <SystemsReadout />
      </section>
      <Section id="services" title={t("services")}>
        {services.length ? (
          <ContentGrid
            prefix=""
            items={services.map((s) => ({
              slug: s.slug,
              title: s.name,
              description: s.intro,
              image: s.hero_image,
            }))}
          />
        ) : (
          <p className="text-text-mute">{t("emptyServices")}</p>
        )}
      </Section>
      {!!home.products.length && (
        <Section id="products" title={t("products")}>
          <ContentGrid
            prefix="/products"
            items={home.products.map(productCard)}
          />
        </Section>
      )}
      {!!home.case_studies.length && (
        <Section id="work" title={t("work")}>
          <ContentGrid prefix="/work" items={home.case_studies.map(caseCard)} />
        </Section>
      )}
      {!!home.industries.length && (
        <Section id="industries" title={t("industries")}>
          <ul className="grid gap-6 sm:grid-cols-3">
            {home.industries.map((i) => (
              <li key={i.slug}>
                <h3 className="text-lg">{i.name}</h3>
                <p className="mt-2 text-text-2">{i.description}</p>
              </li>
            ))}
          </ul>
        </Section>
      )}
      {!!(
        home.tools.length +
        home.certifications.length +
        home.compliance_standards.length
      ) && (
        <Section id="trust" title={t("toolsAndStandards")}>
          <ul className="flex flex-wrap gap-4">
            {[
              ...home.tools,
              ...home.certifications,
              ...home.compliance_standards,
            ].map((i, index) => (
              <li key={index} className="border border-border px-4 py-3">
                {i.name}
              </li>
            ))}
          </ul>
        </Section>
      )}
      {!!home.posts.length && (
        <Section id="posts" title={t("posts")}>
          <ContentGrid prefix="/blog" items={home.posts.map(postCard)} />
        </Section>
      )}
      <Section id="quote" title={t("quote")}>
        <QuoteForm services={services} />
      </Section>
    </Container>
  );
}
