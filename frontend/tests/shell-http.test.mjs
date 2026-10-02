import { test } from "node:test";
import assert from "node:assert/strict";
const base = process.env.TEST_BASE_URL || "http://127.0.0.1:3001";
const fixtures = process.env.PHASE6_FIXTURES === "1";
const locales = ["en", "es", "fr", "de", "zh", "ar"];
const routes = [
  "",
  ...(fixtures
    ? [
        "/digital-marketing",
        "/ai-automation",
        "/custom-software",
        "/web-development",
        "/mobile-development",
        "/cyber-security",
        "/products/test-toolkit",
        "/work/test-case",
        "/blog/test-post",
      ]
    : []),
  "/products",
  "/work",
  "/blog",
  "/about",
  "/contact",
];

test("public destinations have server-rendered content and correct locale metadata", async () => {
  for (const locale of locales) {
    for (const route of routes) {
      const response = await fetch(`${base}/${locale}${route}`);
      assert.equal(response.status, 200, `${locale}${route}`);
      const html = await response.text();
      const rendered = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/g, "");
      assert.match(
        rendered,
        new RegExp(`<html[^>]+lang="${locale === "zh" ? "zh-Hans" : locale}"`),
      );
      assert.match(
        rendered,
        new RegExp(`dir="${locale === "ar" ? "rtl" : "ltr"}"`),
      );
      assert.match(rendered, /<meta name="description" content="[^"]+"/);
      assert.match(html, /application\/ld\+json/);
      assert.match(
        rendered,
        new RegExp(`<link rel="canonical" href="[^\"]+/${locale}${route}"`),
      );
      assert.equal((rendered.match(/<h1\b/g) || []).length, 1);
      assert.match(rendered, /id="main-content"/);
      assert.match(rendered, /<header\b/);
      assert.match(rendered, /<footer\b/);
      assert.match(rendered, new RegExp(`href="/${locale}/products"`));

      assert.match(rendered, /hrefLang="x-default"/i);
      assert.match(rendered, /<title>(?:[^<]+ — )?Automex<\/title>/);
    }
  }
});

test("unknown destinations return 404 instead of a successful placeholder", async () => {
  for (const route of [
    "/en/not-a-page",
    "/ar/not-a-page",
    "/en/work/not-published",
  ]) {
    assert.equal((await fetch(base + route)).status, 404, route);
  }
});

test(
  "filters and pagination preserve selected category",
  { skip: !fixtures },
  async () => {
    const filtered = await (
      await fetch(`${base}/en/products?category=automation`)
    ).text();
    assert.match(filtered, /TEST workflow toolkit/);
    const page2 = await (
      await fetch(`${base}/en/products?category=database&page=2`)
    ).text();
    assert.match(page2, /TEST catalog item/);
    assert.match(page2, /noindex, follow/);
    assert.match(page2, /category=database(?:&amp;|&)page=1/);
    const service = await (await fetch(`${base}/en/ai-automation`)).text();
    assert.match(service, /TEST assistant/);
    assert.match(service, /FAQPage/);
    assert.match(service, /VideoObject/);
    assert.doesNotMatch(service, /<iframe/);
  },
);
