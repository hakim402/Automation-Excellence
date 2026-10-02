import { getTranslations } from "next-intl/server";
import { NavLink } from "@/components/ui/NavLink";
import { Link } from "@/i18n/navigation";
import { serviceSlugs } from "@/lib/navigation";
import type { ServiceSummary } from "@/lib/api-types";

export async function ServicesMenu({ services }: { services: ServiceSummary[] }) {
  const t = await getTranslations("nav");
  return <div className="ax-mega-grid">
    <div><p className="mb-4 text-sm font-semibold text-text-mute">{t("services")}</p>
      <ul className="grid list-none gap-x-8 gap-y-2 sm:grid-cols-2">
        {serviceSlugs.map((slug) => <li key={slug}>
          <NavLink href={`/${slug}`} className="block py-3">
            <span className="block font-semibold">{t(slug)}</span>
            <span className="mt-1 block text-sm font-normal text-text-mute">{services.find(service => service.slug === slug)?.intro || t(`descriptions.${slug}`)}</span>
          </NavLink>
        </li>)}
      </ul>
    </div>
    <div className="ax-products-column">
      <p className="mb-4 text-sm font-semibold text-text-mute">{t("products")}</p>
      <Link href="/products" className="block py-3 font-semibold text-text">{t("browseProducts")}</Link>
      <p className="text-sm text-text-mute">{t("productsDescription")}</p>
    </div>
  </div>;
}
