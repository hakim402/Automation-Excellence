import Image from "next/image";
import { getTranslations, setRequestLocale } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import { getSiteSettings, getTeam } from "@/lib/api";
import { pageMetadata, breadcrumbs } from "@/lib/metadata";
import { JsonLd } from "@/components/ui/JsonLd";
import { Container } from "@/components/ui/Container";
import { PageHero } from "@/components/sections/PageHero";
import { Section } from "@/components/sections/Section";
export const revalidate = 300;
type Props = { params: Promise<{ locale: Locale }> };
export async function generateMetadata({ params }: Props) {
  const { locale } = await params;
  const site = await getSiteSettings(locale);
  const t = await getTranslations({ locale, namespace: "nav" });
  return pageMetadata(
    locale,
    "/about",
    t("about"),
    site?.about_short || t("about"),
  );
}
export default async function About({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [site, team, t, nav] = await Promise.all([
    getSiteSettings(locale),
    getTeam(locale),
    getTranslations("content"),
    getTranslations("nav"),
  ]);
  return (
    <>
      <PageHero title={nav("about")} intro={site?.about_short} />
      <Container className="pb-section-lg">
        {site && (
          <dl className="mb-12 grid gap-8 sm:grid-cols-3">
            {site.service_area && (
              <div>
                <dt className="text-text-mute">{t("serviceArea")}</dt>
                <dd className="mt-2 text-xl">{site.service_area}</dd>
              </div>
            )}
            {site.founded_year && (
              <div>
                <dt>{t("founded")}</dt>
                <dd>{site.founded_year}</dd>
              </div>
            )}
            {site.team_size && (
              <div>
                <dt>{t("teamSize")}</dt>
                <dd>{site.team_size}</dd>
              </div>
            )}
          </dl>
        )}
        {!!team.length && (
          <Section id="team" title={t("team")}>
            <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-3">
              {team.map((person, index) => (
                <article key={index}>
                  {person.photo && (
                    <div className="relative mb-5 aspect-square">
                      <Image
                        src={person.photo}
                        alt={person.name}
                        fill
                        sizes="(max-width:768px) 100vw, 400px"
                        className="object-cover"
                      />
                    </div>
                  )}
                  <h3 className="text-xl">{person.name}</h3>
                  <p className="mt-2 text-text-mute">{person.role}</p>
                  <p className="mt-4 whitespace-pre-line text-text-2">
                    {person.bio}
                  </p>
                  <div className="mt-4 flex gap-4">
                    {person.linkedin && (
                      <a href={person.linkedin} rel="noopener noreferrer">
                        LinkedIn
                      </a>
                    )}
                    {person.github && (
                      <a href={person.github} rel="noopener noreferrer">
                        GitHub
                      </a>
                    )}
                  </div>
                </article>
              ))}
            </div>
          </Section>
        )}
        <JsonLd
          data={breadcrumbs(locale, [
            { name: nav("home"), path: "" },
            { name: nav("about"), path: "/about" },
          ])}
        />
      </Container>
    </>
  );
}
