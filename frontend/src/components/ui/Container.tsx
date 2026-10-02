import type { ComponentPropsWithoutRef } from "react";
export function Container({ className = "", ...props }: ComponentPropsWithoutRef<"div">) {
  return <div className={`mx-auto w-full max-w-(--container-ax) px-gutter ${className}`} {...props} />;
}
