import { getTranslations } from "next-intl/server";
import type { SpecificItem } from "@/lib/api-types";
import { MediaImage } from "@/components/ui/MediaImage";
import { Gallery } from "./Gallery";
export async function SpecificContent({
  groups,
}: {
  groups: Record<string, SpecificItem[]>;
}) {
  const t = await getTranslations("content");
  return (
    <div className="space-y-10">
      {Object.entries(groups)
        .filter(([, items]) => items.length)
        .map(([key, items]) => (
          <div key={key}>
            <h3 className="mb-6 text-xl">{t(`specific.${key}`)}</h3>
            <div className="grid gap-8 md:grid-cols-2">
              {items.map((item, index) => (
                <article
                  key={item.slug || index}
                  className="border-s border-border ps-5"
                >
                  <MediaImage
                    src={
                      item.cover_image ||
                      item.thumbnail ||
                      item.icon_image ||
                      item.logo ||
                      null
                    }
                    alt={item.title || item.name || item.platform || ""}
                  />
                  <h4 className="mt-4 text-lg">
                    {item.title || item.name || item.platform}
                  </h4>
                  {[
                    item.description,
                    item.summary,
                    item.objective,
                    item.results,
                    item.features,
                    item.example_prompt,
                  ]
                    .filter(Boolean)
                    .map((text, i) => (
                      <p
                        key={i}
                        className="mt-3 whitespace-pre-line text-text-2"
                      >
                        {text}
                      </p>
                    ))}
                  {item.client_name && (
                    <p className="mt-3 text-sm text-text-mute">
                      {item.client_name}
                    </p>
                  )}
                  {item.issuer && <p className="mt-3 text-sm">{item.issuer}</p>}
                  {item.platforms && (
                    <p className="mt-3 text-sm">
                      {Array.isArray(item.platforms)
                        ? item.platforms.join(" · ")
                        : item.platforms}
                    </p>
                  )}
                  <dl className="mt-4 space-y-2">
                    {(
                      [
                        "reach",
                        "conversions",
                        "engagement_rate",
                        "downloads",
                        "rating",
                        "follower_count",
                      ] as const
                    )
                      .filter((field) => item[field] != null)
                      .map((field) => (
                        <div key={field} className="flex flex-wrap gap-3">
                          <dt className="text-sm text-text-mute">
                            {t(`metrics.${field}`)}
                          </dt>
                          <dd>
                            <bdi>{item[field]}</bdi>
                          </dd>
                        </div>
                      ))}
                  </dl>
                  <div className="mt-4 flex flex-wrap gap-4">
                    {(
                      [
                        ["url", "visit"],
                        ["external_url", "visit"],
                        ["credential_url", "credential"],
                        ["app_store_url", "appStore"],
                        ["play_store_url", "playStore"],
                        ["file", "download"],
                      ] as const
                    ).map(([field, label]) =>
                      item[field] && /^https?:\/\//.test(item[field]!) ? (
                        <a
                          key={field}
                          href={item[field]!}
                          rel="noopener noreferrer"
                          className="text-sm underline"
                        >
                          {t(label)}
                        </a>
                      ) : null,
                    )}
                  </div>
                  {!!item.screenshots?.length && (
                    <div className="mt-6">
                      <Gallery
                        items={item.screenshots}
                        title={item.name || ""}
                      />
                    </div>
                  )}
                </article>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}
