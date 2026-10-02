import { createElement, type ComponentProps } from "react";
import { createNavigation } from "next-intl/navigation";

import { routing } from "./routing";

/**
 * Locale-aware navigation primitives. Always import Link from here rather
 * than from next/link, so an href never loses its locale prefix.
 */
const navigation = createNavigation(routing);
export const { redirect, usePathname, useRouter, getPathname } = navigation;
// Do not prefetch every catalog/footer destination while the visitor reads a page.
// Client navigation remains available on click; individual links can opt in.
export function Link(props: ComponentProps<typeof navigation.Link>) {
  return createElement(navigation.Link, { prefetch: false, ...props });
}
