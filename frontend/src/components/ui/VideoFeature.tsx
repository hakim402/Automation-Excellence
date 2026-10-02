"use client";
import Image from "next/image";
import { useState } from "react";
import { useTranslations } from "next-intl";
import type { Video } from "@/lib/api-types";
import { videoEmbed } from "@/lib/video";
export function VideoFeature({
  video,
  locale,
}: {
  video: Video;
  locale: string;
}) {
  const [active, setActive] = useState(false);
  const t = useTranslations("content");
  const embed = videoEmbed(video);
  return (
    <figure>
      <div
        className={`relative overflow-hidden border border-border bg-surface ${video.orientation === "portrait" ? "aspect-[9/16]" : "aspect-video"}`}
      >
        {!active ? (
          <button
            type="button"
            className="relative flex size-full items-center justify-center"
            aria-label={`${t("play")}: ${video.title}`}
            onClick={() => setActive(true)}
          >
            {video.poster_image && (
              <Image
                src={video.poster_image}
                alt={video.title}
                fill
                sizes="(max-width: 768px) 100vw, 800px"
                className="object-cover"
              />
            )}
            <span className="relative border border-border bg-bg px-5 py-3 text-text">
              {t("play")}
            </span>
          </button>
        ) : video.source === "file" && video.video_file ? (
          <video
            controls
            playsInline
            preload="metadata"
            poster={video.poster_image || undefined}
            className="size-full"
            aria-label={video.title}
          >
            <source src={video.video_file} />
            {video.captions_url && (
              <track
                kind="captions"
                src={video.captions_url}
                srcLang={locale}
                label={t("captions")}
                default
              />
            )}
          </video>
        ) : embed ? (
          <iframe
            src={embed}
            title={video.title}
            allow="fullscreen; picture-in-picture; encrypted-media"
            allowFullScreen
            className="size-full border-0"
            referrerPolicy="strict-origin-when-cross-origin"
          />
        ) : (
          <p className="p-6">{t("videoUnavailable")}</p>
        )}
      </div>
      <figcaption className="mt-3">
        <p className="font-semibold">{video.title}</p>
        {video.description && (
          <p className="mt-2 text-sm text-text-mute">{video.description}</p>
        )}
        {video.captions_url && (
          <a
            className="mt-2 inline-block text-sm underline"
            href={video.captions_url}
          >
            {t("captions")}
          </a>
        )}
      </figcaption>
    </figure>
  );
}
