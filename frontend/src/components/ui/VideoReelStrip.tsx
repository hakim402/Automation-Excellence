"use client";
import type { Video } from "@/lib/api-types";
import { VideoFeature } from "./VideoFeature";
export function VideoReelStrip({
  videos,
  locale,
  label,
}: {
  videos: Video[];
  locale: string;
  label: string;
}) {
  return (
    <div
      role="region"
      aria-label={label}
      tabIndex={0}
      className="flex snap-x snap-mandatory gap-6 overflow-x-auto pb-6"
      onKeyDown={(event) => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        // Do not steal arrow keys from an embedded player's controls.
        if (event.target !== event.currentTarget) return;
        event.preventDefault();
        const rtl = getComputedStyle(event.currentTarget).direction === "rtl";
        const next = event.key === (rtl ? "ArrowLeft" : "ArrowRight");
        const distance =
          event.currentTarget.clientWidth *
          0.8 *
          (next ? 1 : -1) *
          (rtl ? -1 : 1);
        event.currentTarget.scrollBy({
          left: distance,
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "instant"
            : "smooth",
        });
      }}
    >
      {videos.map((video) => (
        <div key={video.slug} className="w-64 shrink-0 snap-start">
          <VideoFeature video={video} locale={locale} />
        </div>
      ))}
    </div>
  );
}
