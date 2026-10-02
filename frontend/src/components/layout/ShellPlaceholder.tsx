import { getTranslations } from "next-intl/server";
import { Container } from "@/components/ui/Container";
import { Link } from "@/i18n/navigation";
import { buttonClass } from "@/components/ui/Button";
export async function ShellPlaceholder({ route = "home" }: { route?: string }) {
  const t = await getTranslations("shell");
  const nav = await getTranslations("nav");
  return <Container className="py-section-lg">
    <div className="mb-10 flex items-center gap-3 text-sm text-text-mute">
      <span aria-hidden="true" className="size-2 bg-accent" />{t("preview")}
    </div>
    <div className="grid items-start gap-10 md:grid-cols-[1.5fr_1fr]">
      <div className="border-s-2 border-border ps-6">
        <h1 className="text-5xl">{nav(route)}</h1>
        <p className="mt-5 max-w-lg text-lg text-text-2">{t("description")}</p>
        {route !== "home" && <Link href="/" className={`${buttonClass("secondary")} mt-8`}>{t("backHome")}</Link>}
      </div>
      <div aria-hidden="true" className="ax-placeholder-grid"><span /><span /><span /><span /></div>
    </div>
  </Container>;
}
