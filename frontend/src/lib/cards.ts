import type { ProductSummary, CaseSummary, PostSummary } from "./api-types";
export const productCard = (item: ProductSummary) => ({
  slug: item.slug,
  title: item.name,
  description: item.tagline || item.summary,
  image: item.cover_image,
  detail: item.tech_stack.map((tool) => tool.name).join(" · "),
});
export const caseCard = (item: CaseSummary) => ({
  slug: item.slug,
  title: item.title,
  image: item.cover_image,
  eyebrow: item.service?.name,
  description: item.client_name,
});
export const postCard = (item: PostSummary) => ({
  slug: item.slug,
  title: item.title,
  image: item.cover_image,
  eyebrow: item.category?.name,
  description: item.excerpt,
});
