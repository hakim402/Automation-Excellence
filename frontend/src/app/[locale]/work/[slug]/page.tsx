import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import { getCase, getSitemap, validSlug } from "@/lib/api";
import { pageMetadata } from "@/lib/metadata";
import { CasePage } from "@/components/sections/CasePage";
export const revalidate = 300;
export const dynamicParams = true;
export async function generateStaticParams() {
  return (await getSitemap())
    .filter((entry) => entry.locale === "en")
    .map((entry) => new URL(entry.url).pathname)
    .filter((path) => path.startsWith("/en/work/"))
    .map((path) => ({ slug: path.split("/").at(-1)! }));
}
type Props = { params: Promise<{ locale: Locale; slug: string }> };
export async function generateMetadata({ params }: Props) {
  const { locale, slug } = await params;
  if (!validSlug(slug)) notFound();
  const item = await getCase(locale, slug);
  if (!item) notFound();
  return pageMetadata(
    locale,
    `/work/${slug}`,
    item.title,
    item.client_name,
    item,
  );
}
export default async function Page({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  if (!validSlug(slug)) notFound();
  const item = await getCase(locale, slug);
  if (!item) notFound();
  return <CasePage item={item} locale={locale} />;
}
