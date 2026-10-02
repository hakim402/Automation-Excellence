import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";
const locales = ["en", "es", "fr", "de", "zh", "ar"];
const localeTags = {
  en: "en",
  es: "es",
  fr: "fr",
  de: "de",
  zh: "zh-Hans",
  ar: "ar",
};
function load(file, imports) {
  const code = ts.transpileModule(
    fs.readFileSync(new URL(`../src/${file}`, import.meta.url), "utf8"),
    {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
      },
    },
  ).outputText;
  const exports = {};
  new Function("require", "exports", code)((name) => {
    if (name in imports) return imports[name];
    throw Error(name);
  }, exports);
  return exports;
}
const seo = load("lib/seo.ts", { "@/i18n/routing": { locales, localeTags } });
test("sitemap uses frontend origin, six alternate locales and source modification time", () => {
  const entries = locales.map((locale) => ({
    locale,
    url: `https://backend.test/${locale}/blog/example`,
    lastmod: "2026-10-02T00:00:00Z",
    alternates: {
      ...Object.fromEntries(
        locales.map((code) => [
          code,
          `https://backend.test/${code}/blog/example`,
        ]),
      ),
      "x-default": "https://backend.test/en/blog/example",
    },
  }));
  const result = seo.sitemapEntries(entries, "https://automex.test");
  assert.equal(result.length, 6);
  assert.equal(result[4].url, "https://automex.test/zh/blog/example");
  assert.equal(
    result[0].alternates.languages["zh-Hans"],
    "https://automex.test/zh/blog/example",
  );
  assert.equal(
    result[0].alternates.languages["x-default"],
    "https://automex.test/en/blog/example",
  );
  assert.equal(result[0].lastModified, entries[0].lastmod);
});
test("analytics stays disabled for missing or malformed IDs and excludes URL personal data", () => {
  for (const id of ["", "UA-12345", "G-<script>", "G-123456';alert(1)"])
    assert.equal(seo.validMeasurementId(id), false);
  assert.equal(seo.validMeasurementId("G-1234567890"), true);
  assert.deepEqual(
    seo.analyticsPage(
      "https://automex.test",
      "/en/contact?email=private@example.test#token",
    ),
    { page_location: "https://automex.test/en/contact", page_referrer: "" },
  );
});
test("metadata falls back to site social image and returns full localized alternates", async () => {
  const { pageMetadata } = load("lib/metadata.ts", {
    "server-only": {},
    next: {},
    "./api": {
      getSiteSettings: async () => ({
        default_og_image: "https://media.test/social.png",
        favicon: "https://media.test/icon.png",
      }),
    },
    "./seo": seo,
    "./env": { SITE_URL: "https://automex.test" },
    "@/i18n/routing": { locales, localeTags },
  });
  const result = await pageMetadata("ar", "/contact", "تواصل معنا", "وصف");
  assert.equal(result.alternates.canonical, "https://automex.test/ar/contact");
  assert.equal(Object.keys(result.alternates.languages).length, 7);
  assert.equal(result.openGraph.locale, "ar_AR");
  assert.equal(result.openGraph.images[0].url, "https://media.test/social.png");
  assert.equal(result.twitter.card, "summary_large_image");
});
