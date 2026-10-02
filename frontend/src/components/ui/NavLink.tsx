"use client";
import { Link, usePathname } from "@/i18n/navigation";
import type { ReactNode } from "react";
export function NavLink({ href, children, className = "" }: { href: string; children: ReactNode; className?: string }) {
  const pathname = usePathname();
  return <Link href={href} aria-current={pathname === href ? "page" : undefined} className={`ax-nav-link ${className}`}>{children}</Link>;
}
