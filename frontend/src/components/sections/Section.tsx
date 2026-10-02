import type { ReactNode } from "react";
export function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-title`}
      className="ax-section border-t border-border py-section-sm"
    >
      <h2 id={`${id}-title`} className="mb-8 text-3xl">
        {title}
      </h2>
      {children}
    </section>
  );
}
