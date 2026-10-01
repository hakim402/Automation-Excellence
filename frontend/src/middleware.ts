import createMiddleware from "next-intl/middleware";

import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Run on content routes only. Excludes /api, Next internals, and anything
  // with a file extension (images, robots.txt, sitemap.xml, fonts).
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
