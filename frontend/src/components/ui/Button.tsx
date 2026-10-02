import type { ComponentPropsWithoutRef } from "react";
export function buttonClass(variant: "primary" | "secondary" = "primary") {
  return `inline-flex min-h-11 items-center justify-center rounded-sm border px-5 py-2 text-sm font-semibold transition-colors ${variant === "primary" ? "border-accent bg-accent text-on-accent hover:underline" : "border-border bg-surface text-text hover:border-link"}`;
}
export function Button({ className = "", variant = "primary", type = "button", ...props }: ComponentPropsWithoutRef<"button"> & { variant?: "primary" | "secondary" }) {
  return <button type={type} className={`${buttonClass(variant)} disabled:cursor-not-allowed disabled:bg-border disabled:text-text-mute ${className}`} {...props} />;
}
