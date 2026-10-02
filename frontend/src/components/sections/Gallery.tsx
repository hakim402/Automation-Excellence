import type { GalleryImage } from "@/lib/api-types";
import { MediaImage } from "@/components/ui/MediaImage";
export function Gallery({
  items,
  title,
}: {
  items: GalleryImage[];
  title: string;
}) {
  return (
    <div className="grid gap-8 md:grid-cols-2">
      {items.map((item, index) => (
        <figure key={index}>
          <MediaImage src={item.image} alt={item.caption || title} />
          {item.caption && (
            <figcaption className="mt-3 text-sm text-text-mute">
              {item.caption}
            </figcaption>
          )}
        </figure>
      ))}
    </div>
  );
}
