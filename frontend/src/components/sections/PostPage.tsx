import { getTranslations } from "next-intl/server";
import type { Locale } from "@/i18n/routing";
import type { PostDetail } from "@/lib/api-types";
import { getPosts } from "@/lib/api";
import { postCard } from "@/lib/cards";
import { SITE_URL } from "@/lib/env";
import { breadcrumbs } from "@/lib/metadata";
import { Link } from "@/i18n/navigation";
import { JsonLd } from "@/components/ui/JsonLd";
import { Container } from "@/components/ui/Container";
import { RichText } from "@/components/ui/RichText";
import { PageHero } from "./PageHero";
import { Section } from "./Section";
import { ContentGrid } from "./ContentGrid";
export async function PostPage({
  post,
  locale,
}: {
  post: PostDetail;
  locale: Locale;
}) {
  const t = await getTranslations("content");
  const nav = await getTranslations("nav");
  const related = (
    await getPosts(
      locale,
      post.category ? { category: post.category.slug } : {},
    )
  ).results
    .filter((p) => p.slug !== post.slug)
    .slice(0, 3);
  return (
    <article>
      <PageHero
        title={post.title}
        intro={post.excerpt}
        image={post.cover_image}
      />
      <Container className="pb-section-lg">
        <div className="mx-auto max-w-3xl">
          <div className="mb-8 flex flex-wrap gap-4 text-sm text-text-mute">
            {post.author && <span>{post.author.name}</span>}
            {post.published_at && (
              <time dateTime={post.published_at}>
                {new Intl.DateTimeFormat(locale, {
                  dateStyle: "long",
                  timeZone: "UTC",
                }).format(new Date(post.published_at))}
              </time>
            )}
            <span>{t("reading", { minutes: post.reading_minutes })}</span>
          </div>
          <RichText html={post.body} />
          {post.service && (
            <p className="mt-10">
              <Link href={`/${post.service.slug}`}>{post.service.name}</Link>
            </p>
          )}
          {!!post.tags.length && (
            <ul className="mt-6 flex flex-wrap gap-3">
              {post.tags.map((tag) => (
                <li
                  key={tag.slug}
                  className="border border-border px-3 py-1 text-sm"
                >
                  {tag.name}
                </li>
              ))}
            </ul>
          )}
        </div>
        {!!related.length && (
          <div className="mt-section-md">
            <Section id="related" title={t("posts")}>
              <ContentGrid prefix="/blog" items={related.map(postCard)} />
            </Section>
          </div>
        )}
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            headline: post.title,
            description: post.excerpt,
            datePublished: post.published_at || undefined,
            dateModified: post.updated_at,
            image: post.cover_image || undefined,
            author: post.author
              ? { "@type": "Person", name: post.author.name }
              : undefined,
            publisher: { "@id": `${SITE_URL}/#organization` },
            mainEntityOfPage: `${SITE_URL}/${locale}/blog/${post.slug}`,
          }}
        />
        <JsonLd
          data={breadcrumbs(locale, [
            { name: nav("home"), path: "" },
            { name: nav("blog"), path: "/blog" },
            { name: post.title, path: `/blog/${post.slug}` },
          ])}
        />
      </Container>
    </article>
  );
}
