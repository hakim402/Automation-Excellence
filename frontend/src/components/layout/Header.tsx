import { getTranslations } from "next-intl/server";
import { Brand } from "./Brand";
import { ServicesMenu } from "./ServicesMenu";
import { Container } from "@/components/ui/Container";
import { Disclosure } from "@/components/ui/Disclosure";
import { LocaleSwitcher } from "@/components/ui/LocaleSwitcher";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { NavLink } from "@/components/ui/NavLink";
import { serviceSlugs } from "@/lib/navigation";
import type { ServiceSummary, SiteSettings } from "@/lib/api-types";

export async function Header({ site, services }: { site: SiteSettings | null; services: ServiceSummary[] }) {
  const t = await getTranslations("nav");
  return <header className="ax-header border-b border-border bg-bg">
    <Container>
      <div className="flex min-h-24 flex-wrap items-center justify-between gap-x-6 gap-y-2 py-4">
        <Brand site={site} />
        <div className="flex flex-wrap items-center gap-3 sm:gap-5">
          <div className="ax-wide-only"><Disclosure label={t("explore")} panelClassName="ax-mega-panel"><ServicesMenu services={services} /></Disclosure></div>
          <LocaleSwitcher /><div className="hidden sm:block"><ThemeToggle /></div>
        </div>
      </div>
      <nav aria-label={t("primary")} className="ax-primary flex items-center gap-6 border-t border-border">
        <NavLink href="/">{t("home")}</NavLink>
        <div className="ax-compact-only"><Disclosure label={t("services")} panelClassName="ax-mega-panel"><ServicesMenu services={services} /></Disclosure></div>
        {serviceSlugs.map(slug => <NavLink key={slug} href={`/${slug}`} className="ax-wide-only">{t(slug)}</NavLink>)}
        <NavLink href="/about">{t("about")}</NavLink>
        <NavLink href="/contact">{t("contact")}</NavLink>
      </nav>
    </Container>
  </header>;
}
