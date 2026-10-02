import type { Video } from "./api-types";
export function videoEmbed(video: Video): string | null {
  try {
    const url = new URL(video.external_url);
    if (url.protocol !== "https:") return null;
    if (
      video.source === "youtube" &&
      ["youtu.be", "youtube.com", "www.youtube.com", "m.youtube.com"].includes(
        url.hostname,
      )
    ) {
      const id =
        url.hostname === "youtu.be"
          ? url.pathname.slice(1)
          : url.searchParams.get("v") || url.pathname.split("/").at(-1);
      return id && /^[a-zA-Z0-9_-]{11}$/.test(id)
        ? `https://www.youtube-nocookie.com/embed/${id}?cc_load_policy=1`
        : null;
    }
    if (
      video.source === "vimeo" &&
      ["vimeo.com", "www.vimeo.com", "player.vimeo.com"].includes(url.hostname)
    ) {
      const id = url.pathname.split("/").at(-1);
      return id && /^\d+$/.test(id)
        ? `https://player.vimeo.com/video/${id}`
        : null;
    }
  } catch {
    /* Unsupported provider URL is rendered as unavailable. */
  }
  return null;
}
