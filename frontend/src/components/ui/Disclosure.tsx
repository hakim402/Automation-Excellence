"use client";
import { useEffect, useRef, type ReactNode } from "react";

/** Native disclosure keeps links reachable without JS; JS adds dismissal. */
export function Disclosure({ label, children, className = "", panelClassName = "" }: {
  label: string; children: ReactNode; className?: string; panelClassName?: string;
}) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    function dismiss(event: KeyboardEvent) {
      if (event.key === "Escape" && node?.open) {
        node.open = false;
        node.querySelector("summary")?.focus();
      }
    }
    function outside(event: PointerEvent) {
      if (node?.open && event.target instanceof Node && !node.contains(event.target)) node.open = false;
    }
    document.addEventListener("keydown", dismiss);
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("keydown", dismiss);
      document.removeEventListener("pointerdown", outside);
    };
  }, []);
  return (
    <details ref={ref} className={`ax-disclosure ${className}`} onBlur={(event) => {
      if (event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false;
    }}>
      <summary className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-medium">
        {label}<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m4 6 4 4 4-4" stroke="currentColor" strokeWidth="1.5" /></svg>
      </summary>
      <div className={panelClassName} onClick={(event) => {
        if (event.target instanceof Element && event.target.closest("a")) {
          if (ref.current) ref.current.open = false;
        }
      }}>{children}</div>
    </details>
  );
}
