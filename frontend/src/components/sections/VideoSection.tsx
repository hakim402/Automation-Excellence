import { getTranslations } from "next-intl/server";
import type { Video } from "@/lib/api-types";
import { VideoFeature } from "@/components/ui/VideoFeature";
import { VideoReelStrip } from "@/components/ui/VideoReelStrip";
import { JsonLd } from "@/components/ui/JsonLd";
import { videoEmbed } from "@/lib/video";
export async function VideoSection({
  videos,
  locale,
}: {
  videos: Video[];
  locale: string;
}) {
  const t = await getTranslations("content");
  const landscape = videos.filter((video) => video.orientation === "landscape");
  const portrait = videos.filter((video) => video.orientation === "portrait");
  return (
    <div className="space-y-10">
      {landscape.map((video) => (
        <VideoFeature key={video.slug} video={video} locale={locale} />
      ))}
      {portrait.length > 0 && (
        <VideoReelStrip videos={portrait} locale={locale} label={t("videos")} />
      )}
      {videos.map((video) => (
        <JsonLd
          key={video.slug}
          data={{
            "@context": "https://schema.org",
            "@type": "VideoObject",
            name: video.title,
            description: video.description || video.title,
            ...(video.poster_image && { thumbnailUrl: video.poster_image }),
            ...(video.published_at && { uploadDate: video.published_at }),
            ...(video.duration_seconds && {
              duration: `PT${video.duration_seconds}S`,
            }),
            ...(video.source === "file"
              ? { contentUrl: video.video_file }
              : { embedUrl: videoEmbed(video) || undefined }),
          }}
        />
      ))}
    </div>
  );
}
