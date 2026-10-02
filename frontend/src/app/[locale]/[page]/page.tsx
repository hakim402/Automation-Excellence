import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import { ShellPlaceholder } from "@/components/layout/ShellPlaceholder";
import { shellRoutes, isShellRoute } from "@/lib/navigation";
import { shellMetadata } from "@/lib/metadata";
import type { Locale } from "@/i18n/routing";
export const revalidate = 300;
export const dynamicParams = false;
export function generateStaticParams() { return shellRoutes.map(page => ({ page })); }
type Props = { params: Promise<{ locale: Locale; page: string }> };
export async function generateMetadata({ params }: Props) {
  const { locale, page } = await params;
  if (!isShellRoute(page)) notFound();
  return shellMetadata(locale, page);
}
export default async function Placeholder({ params }: Props) {
  const { locale, page } = await params;
  if (!isShellRoute(page)) notFound();
  setRequestLocale(locale);
  return <ShellPlaceholder route={page} />;
}
