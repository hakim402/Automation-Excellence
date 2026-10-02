import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Container } from "@/components/ui/Container";
import { buttonClass } from "@/components/ui/Button";
export default async function NotFound() {
  const t = await getTranslations("shell");
  return (
    <Container className="py-section-lg">
      <p className="ax-mono mb-4 text-text-mute">404</p>
      <h1 className="text-4xl">{t("notFound")}</h1>
      <Link href="/" className={`${buttonClass("secondary")} mt-8`}>
        {t("backHome")}
      </Link>
    </Container>
  );
}
