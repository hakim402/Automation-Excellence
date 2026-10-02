export const serviceSlugs = [
  "digital-marketing", "ai-automation", "custom-software",
  "web-development", "mobile-development", "cyber-security",
] as const;
export const shellRoutes = [...serviceSlugs, "products", "work", "blog", "about", "contact"] as const;
export type ShellRoute = (typeof shellRoutes)[number];
export function isShellRoute(value: string): value is ShellRoute {
  return (shellRoutes as readonly string[]).includes(value);
}
