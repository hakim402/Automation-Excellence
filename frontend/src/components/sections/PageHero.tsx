import { Link } from "@/i18n/navigation";
import { Container } from "@/components/ui/Container";
import { MediaImage } from "@/components/ui/MediaImage";
import { buttonClass } from "@/components/ui/Button";
import { getTranslations } from "next-intl/server";
export async function PageHero({
  title,
  intro,
  image,
  quote = false,
}: {
  title: string;
  intro?: string;
  image?: string | null;
  quote?: boolean;
}) {
  const t = await getTranslations("content");
  return (
    <Container className="py-section-md">
      <div
        className={
          image ? "grid items-center gap-10 lg:grid-cols-2" : "max-w-3xl"
        }
      >
        <div>
          <h1 className="text-5xl">{title}</h1>
          {intro && (
            <p className="mt-6 max-w-(--ax-measure) text-lg leading-relaxed text-text-2">
              {intro}
            </p>
          )}
          {quote && (
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="#quote" className={buttonClass()}>
                {t("quote")}
              </a>
              <Link href="/work" className={buttonClass("secondary")}>
                {t("seeWork")}
              </Link>
            </div>
          )}
        </div>
        {image && <MediaImage src={image} alt={title} priority />}
      </div>
    </Container>
  );
}
