import { setRequestLocale } from "next-intl/server";
import { ShellPlaceholder } from "@/components/layout/ShellPlaceholder";
import { shellMetadata } from "@/lib/metadata";
import type { Locale } from "@/i18n/routing";
export const revalidate = 300;
export async function generateMetadata({ params }: { params: Promise<{ locale: Locale }> }) {
  return shellMetadata((await params).locale);
}
export default async function Home({ params }: { params: Promise<{ locale: Locale }> }) {
  setRequestLocale((await params).locale);
  return <ShellPlaceholder />;
}
