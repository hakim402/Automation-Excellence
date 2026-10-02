import Image from "next/image";
import { Link } from "@/i18n/navigation";
import type { SiteSettings } from "@/lib/api-types";
export function Brand({ site }: { site: SiteSettings | null }) {
  const name = site?.company_name || "Automex";
  return <Link href="/" aria-label={name} dir="ltr" className="ax-brand inline-flex min-h-11 items-center text-2xl font-semibold tracking-tight text-text no-underline">
    {site?.logo && site.logo_dark ? <span className="relative block h-10 w-40">
      <Image src={site.logo_dark} alt={name} fill sizes="160px" className="ax-logo-light object-contain object-start" />
      <Image src={site.logo} alt={name} fill sizes="160px" className="ax-logo-dark object-contain object-start" />
    </span> : <span>{name}<span aria-hidden="true" className="text-accent">.</span></span>}
  </Link>;
}
