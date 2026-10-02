import { getTranslations } from "next-intl/server";
import { Brand } from "./Brand";
import { Container } from "@/components/ui/Container";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { Link } from "@/i18n/navigation";
import { serviceSlugs } from "@/lib/navigation";
import type { SiteSettings } from "@/lib/api-types";

export async function Footer({ site }: { site: SiteSettings | null }) {
  const t = await getTranslations("nav");
  const f = await getTranslations("footer");
  const socials = site ? [
    ["LinkedIn", site.linkedin_url], ["GitHub", site.github_url], ["Instagram", site.instagram_url],
    ["YouTube", site.youtube_url], ["Facebook", site.facebook_url], ["X", site.x_url],
  ].filter(([, url]) => /^https?:\/\//.test(url)) : [];
  return <footer className="border-t border-border bg-surface">
    <Container className="py-section-sm">
      <div className="grid gap-10 md:grid-cols-2 xl:grid-cols-[1.25fr_1fr_.7fr_1.2fr]">
        <div><Brand site={site} />{site?.tagline && <p className="mt-3 max-w-xs text-sm text-text-mute">{site.tagline}</p>}
          {socials.length > 0 && <ul className="mt-5 flex flex-wrap gap-x-4 gap-y-2">{socials.map(([name, url]) => <li key={name}><a href={url} rel="noopener noreferrer" className="text-sm">{name}</a></li>)}</ul>}
        </div>
        <nav aria-label={f("services")}><h2 className="mb-4 text-sm">{t("services")}</h2><ul className="space-y-2 text-sm">{serviceSlugs.map(slug => <li key={slug}><Link href={`/${slug}`} className="text-text-2 hover:underline">{t(slug)}</Link></li>)}</ul></nav>
        <nav aria-label={f("company")}><h2 className="mb-4 text-sm">{f("company")}</h2><ul className="space-y-2 text-sm">{(["about", "products", "work", "blog", "contact"] as const).map(key => <li key={key}><Link href={`/${key}`} className="text-text-2 hover:underline">{t(key)}</Link></li>)}</ul></nav>
        {site && <div><h2 className="mb-4 text-sm">{f("contact")}</h2><address className="space-y-3 text-sm not-italic text-text-2">
          {site.email && <p><a href={`mailto:${site.email}`}><bdi>{site.email}</bdi></a></p>}
          {site.phone_us && <p><span className="me-2 text-text-mute">{f("us")}</span><a href={`tel:${site.phone_us.replace(/[^+\d]/g, "")}`}><bdi dir="ltr">{site.phone_us}</bdi></a></p>}
          {site.phone_af && <p><span className="me-2 text-text-mute">{f("af")}</span><a href={`tel:${site.phone_af.replace(/[^+\d]/g, "")}`}><bdi dir="ltr">{site.phone_af}</bdi></a></p>}
          <p><bdi>{[site.address_line_1, site.address_line_2].filter(Boolean).join(", ")}</bdi><br /><bdi>{[site.city, site.state, site.postal_code].filter(Boolean).join(" ")}</bdi><br /><bdi>{site.country}</bdi></p>
        </address></div>}
      </div>
      <div className="mt-10 flex flex-wrap items-center justify-between gap-5 border-t border-border pt-6">
        <p className="text-xs text-text-mute">© {new Date().getUTCFullYear()} {site?.company_name || "Automex"}. {f("rights")}</p>
        <ThemeToggle />
      </div>
    </Container>
  </footer>;
}
