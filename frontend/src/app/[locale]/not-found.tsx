import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export default async function NotFound() {
  const t = await getTranslations("common");

  return (
    <main className="mx-auto flex min-h-screen max-w-(--container-ax) flex-col items-start justify-center gap-4 px-gutter">
      <p className="ax-mono text-2xs tracking-wide text-ax-slate">404</p>
      <h1 className="text-3xl text-ax-paper">{t("brand")}</h1>
      <Link href="/" className="text-ax-cyan underline">
        {t("brand")}
      </Link>
    </main>
  );
}
