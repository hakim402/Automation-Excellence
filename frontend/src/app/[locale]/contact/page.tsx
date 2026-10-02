import { getTranslations, setRequestLocale } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import { getSiteSettings, getServices } from "@/lib/api";
import { pageMetadata, breadcrumbs } from "@/lib/metadata";
import { JsonLd } from "@/components/ui/JsonLd";
import { Container } from "@/components/ui/Container";
import { PageHero } from "@/components/sections/PageHero";
import { QuoteForm } from "@/components/sections/QuoteForm";
export const revalidate = 300;
type Props = { params: Promise<{ locale: Locale }> };
export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "nav" });
  return pageMetadata(locale, "/contact", t("contact"), t("contact"));
}
export default async function Contact({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [site, services, t, nav, f] = await Promise.all([
    getSiteSettings(locale),
    getServices(locale),
    getTranslations("content"),
    getTranslations("nav"),
    getTranslations("footer"),
  ]);
  const address = site
    ? [
        site.address_line_1,
        site.address_line_2,
        site.city,
        site.state,
        site.postal_code,
        site.country,
      ]
        .filter(Boolean)
        .join(", ")
    : "";
  return (
    <>
      <PageHero title={nav("contact")} intro={site?.response_time} />
      <Container className="grid gap-12 pb-section-lg lg:grid-cols-[1.6fr_1fr]">
        <div>
          <h2 className="mb-8 text-2xl">{t("quote")}</h2>
          <QuoteForm services={services} />
        </div>
        {site && (
          <aside className="min-w-0">
            <h2 className="mb-6 text-2xl">{f("contact")}</h2>
            <address className="space-y-5 not-italic">
              {site.email && (
                <p>
                  <a href={`mailto:${site.email}`}>
                    <bdi>{site.email}</bdi>
                  </a>
                </p>
              )}
              {[
                [site.phone_us, f("us")],
                [site.phone_af, f("af")],
              ]
                .filter(([phone]) => phone)
                .map(([phone, label]) => (
                  <p key={label}>
                    <span className="me-3 text-text-mute">{label}</span>
                    <a href={`tel:${phone.replace(/[^+\d]/g, "")}`}>
                      <bdi dir="ltr">{phone}</bdi>
                    </a>
                  </p>
                ))}
              {address && (
                <p>
                  <bdi>{address}</bdi>
                </p>
              )}
            </address>
            {address && (
              <iframe
                title={t("map")}
                src={`https://maps.google.com/maps?q=${encodeURIComponent(address)}&output=embed`}
                loading="lazy"
                referrerPolicy="no-referrer"
                className="mt-8 aspect-square w-full border border-border"
              />
            )}
          </aside>
        )}
        <JsonLd
          data={breadcrumbs(locale, [
            { name: nav("home"), path: "" },
            { name: nav("contact"), path: "/contact" },
          ])}
        />
      </Container>
    </>
  );
}
