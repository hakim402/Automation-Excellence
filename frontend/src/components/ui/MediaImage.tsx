import Image from "next/image";
export function MediaImage({
  src,
  alt,
  priority = false,
}: {
  src: string | null;
  alt: string;
  priority?: boolean;
}) {
  if (!src) return null;
  return (
    <div className="relative aspect-video overflow-hidden border border-border bg-surface">
      <Image
        src={src}
        alt={alt}
        fill
        sizes="(max-width: 768px) 100vw, 900px"
        priority={priority}
        fetchPriority={priority ? "high" : undefined}
        className="object-cover"
      />
    </div>
  );
}
