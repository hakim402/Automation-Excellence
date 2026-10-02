import { Link } from "@/i18n/navigation";
import { MediaImage } from "@/components/ui/MediaImage";
export interface ContentCard {
  slug: string;
  title: string;
  description?: string;
  image?: string | null;
  eyebrow?: string;
  detail?: string;
}
export function ContentGrid({
  items,
  prefix,
  headingLevel = 3,
}: {
  items: ContentCard[];
  prefix: string;
  headingLevel?: 2 | 3;
}) {
  const Heading = headingLevel === 2 ? "h2" : "h3";
  return (
    <div className="grid gap-x-8 gap-y-12 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <article
          key={item.slug}
          className="min-w-0 border-b border-border pb-6"
        >
          {item.image && (
            <Link
              href={`${prefix}/${item.slug}`}
              tabIndex={-1}
              aria-hidden="true"
            >
              <MediaImage src={item.image} alt={item.title} />
            </Link>
          )}
          {item.eyebrow && (
            <p className="mt-5 text-sm text-text-mute">{item.eyebrow}</p>
          )}
          <Heading className="mt-4 text-xl">
            <Link
              href={`${prefix}/${item.slug}`}
              className="text-text hover:text-link"
            >
              {item.title}
            </Link>
          </Heading>
          {item.description && (
            <p className="mt-3 text-text-2">{item.description}</p>
          )}
          {item.detail && (
            <p className="mt-4 text-sm text-text-mute">{item.detail}</p>
          )}
        </article>
      ))}
    </div>
  );
}
