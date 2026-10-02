import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import type { Locale } from "@/i18n/routing";
import { Link } from "@/i18n/navigation";
import {
  ApiError,
  getCategories,
  getProducts,
  getCases,
  getPosts,
  getServices,
} from "@/lib/api";
import { productCard, caseCard, postCard } from "@/lib/cards";
import { Container } from "@/components/ui/Container";
import { JsonLd } from "@/components/ui/JsonLd";
import { breadcrumbs } from "@/lib/metadata";
import { PageHero } from "./PageHero";
import { ContentGrid } from "./ContentGrid";
export type ListingKind = "products" | "work" | "blog";
export type Search = Record<string, string | string[] | undefined>;
export async function ListingPage({
  kind,
  locale,
  query,
}: {
  kind: ListingKind;
  locale: Locale;
  query: Search;
}) {
  const t = await getTranslations("content");
  const nav = await getTranslations("nav");
  const single = (key: string) =>
    typeof query[key] === "string" ? (query[key] as string) : "";
  const raw = single("page") || "1";
  if (!/^[1-9]\d{0,5}$/.test(raw)) notFound();
  const page = Number(raw);
  const filterName = kind === "work" ? "service" : "category";
  const filter = single(filterName);
  const categories =
    kind === "blog"
      ? (await getCategories(locale)).map((i) => ({
          value: i.slug,
          label: i.name,
        }))
      : kind === "work"
        ? (await getServices(locale)).map((i) => ({
            value: i.slug,
            label: i.name,
          }))
        : [
            "database",
            "web-app",
            "mobile-app",
            "dashboard",
            "automation",
            "template",
            "integration",
          ].map((value) => ({ value, label: t(`categories.${value}`) }));
  let result;
  try {
    if (kind === "products") {
      const data = await getProducts(locale, { category: filter, page });
      result = {
        ...data,
        items: data.results.map((i) => ({
          ...productCard(i),
          eyebrow: t(`categories.${i.category}`),
          detail: [t(`delivery.${i.delivery}`), productCard(i).detail]
            .filter(Boolean)
            .join(" · "),
        })),
      };
    } else if (kind === "work") {
      const data = await getCases(locale, { service: filter, page });
      result = { ...data, items: data.results.map(caseCard) };
    } else {
      const data = await getPosts(locale, { category: filter, page });
      result = { ...data, items: data.results.map(postCard) };
    }
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
  const href = (n: number) => ({
    pathname: `/${kind}`,
    query: { ...(filter ? { [filterName]: filter } : {}), page: String(n) },
  });
  return (
    <>
      <PageHero title={nav(kind)} />
      <Container className="pb-section-lg">
        <form
          action={`/${locale}/${kind}`}
          className="ax-form mb-10 flex flex-wrap items-end gap-4"
        >
          <label>
            {t("filter")}
            <select name={filterName} defaultValue={filter}>
              <option value="">{t("all")}</option>
              {categories.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <button className="min-h-11 border border-border bg-surface px-5">
            {t("apply")}
          </button>
        </form>
        {result.items.length ? (
          <ContentGrid items={result.items} prefix={`/${kind}`} />
        ) : (
          <p className="border-t border-border py-10 text-text-mute">
            {t("empty")}
          </p>
        )}
        <nav
          aria-label={t("pagination")}
          className="mt-10 flex flex-wrap items-center gap-6"
        >
          {result.previous && (
            <Link href={href(page - 1)}>{t("previous")}</Link>
          )}
          <span className="text-sm text-text-mute">{t("page", { page })}</span>
          {result.next && <Link href={href(page + 1)}>{t("next")}</Link>}
        </nav>
        <JsonLd
          data={breadcrumbs(locale, [
            { name: nav("home"), path: "" },
            { name: nav(kind), path: `/${kind}` },
          ])}
        />
      </Container>
    </>
  );
}
