import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import { getService, getServices, validSlug } from "@/lib/api";
import { pageMetadata } from "@/lib/metadata";
import { ServicePage } from "@/components/sections/ServicePage";
import type { Locale } from "@/i18n/routing";
export const revalidate = 300;
export const dynamicParams = true;
export async function generateStaticParams() {
  return (await getServices("en")).map((service) => ({ page: service.slug }));
}
type Props = { params: Promise<{ locale: Locale; page: string }> };
export async function generateMetadata({ params }: Props) {
  const { locale, page } = await params;
  if (!validSlug(page)) notFound();
  const service = await getService(locale, page);
  if (!service) notFound();
  return pageMetadata(locale, `/${page}`, service.name, service.intro, service);
}
export default async function Page({ params }: Props) {
  const { locale, page } = await params;
  setRequestLocale(locale);
  if (!validSlug(page)) notFound();
  const [service, services] = await Promise.all([
    getService(locale, page),
    getServices(locale),
  ]);
  if (!service) notFound();
  return <ServicePage service={service} services={services} locale={locale} />;
}
