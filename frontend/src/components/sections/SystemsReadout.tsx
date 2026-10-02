import { getTranslations } from "next-intl/server";
export async function SystemsReadout() {
  const t = await getTranslations("content");
  return (
    <div className="ax-readout border border-border bg-surface p-6 sm:p-8">
      <p className="mb-8 text-sm text-text-mute">{t("illustration")}</p>
      <ol className="space-y-0">
        {["connect", "process", "deliver"].map((key, index) => (
          <li
            key={key}
            className="ax-readout-step flex items-center gap-5 border-t border-border py-6"
          >
            <span
              aria-hidden="true"
              style={{ animationDelay: `${index * 2}s` }}
              className="ax-status-dot size-2 bg-success"
            />
            <span className="text-xl">{t(`readout.${key}`)}</span>
            <span aria-hidden="true" className="ms-auto h-px w-12 bg-border" />
          </li>
        ))}
      </ol>
    </div>
  );
}
