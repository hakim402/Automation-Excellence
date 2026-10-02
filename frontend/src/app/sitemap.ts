import type { MetadataRoute } from "next";
import { getSitemap } from "@/lib/api";
import { sitemapEntries } from "@/lib/seo";
import { SITE_URL } from "@/lib/env";
export const revalidate = 300;
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  return sitemapEntries(await getSitemap(), SITE_URL);
}
