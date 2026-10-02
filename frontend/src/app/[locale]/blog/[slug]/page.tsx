import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import { getPost, getSitemap, validSlug } from "@/lib/api";
import { pageMetadata } from "@/lib/metadata";
import { PostPage } from "@/components/sections/PostPage";
export const revalidate = 300;
export const dynamicParams = true;
export async function generateStaticParams() {
  return (await getSitemap())
    .filter((entry) => entry.locale === "en")
    .map((entry) => new URL(entry.url).pathname)
    .filter((path) => path.startsWith("/en/blog/"))
    .map((path) => ({ slug: path.split("/").at(-1)! }));
}
type Props = { params: Promise<{ locale: Locale; slug: string }> };
export async function generateMetadata({ params }: Props) {
  const { locale, slug } = await params;
  if (!validSlug(slug)) notFound();
  const item = await getPost(locale, slug);
  if (!item) notFound();
  return pageMetadata(locale, `/blog/${slug}`, item.title, item.excerpt, item);
}
export default async function Page({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  if (!validSlug(slug)) notFound();
  const item = await getPost(locale, slug);
  if (!item) notFound();
  return <PostPage post={item} locale={locale} />;
}
