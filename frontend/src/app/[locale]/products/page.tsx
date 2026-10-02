import { getTranslations, setRequestLocale } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import { ListingPage, type Search } from "@/components/sections/ListingPage";
import { pageMetadata } from "@/lib/metadata";
export const revalidate = 300;
type Props = {
  params: Promise<{ locale: Locale }>;
  searchParams: Promise<Search>;
};
export async function generateMetadata({ params, searchParams }: Props) {
  const { locale } = await params;
  const query = await searchParams;
  const t = await getTranslations({ locale, namespace: "nav" });
  return pageMetadata(locale, "/products", t("products"), t("products"), {
    noindex: Object.keys(query).length > 0,
  });
}
export default async function Page({ params, searchParams }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  return (
    <ListingPage kind="products" locale={locale} query={await searchParams} />
  );
}
