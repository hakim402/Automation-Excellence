import { test } from "node:test";
import assert from "node:assert/strict";
const base = process.env.TEST_BASE_URL || "http://localhost:3001";
const locales = ["en", "es", "fr", "de", "zh", "ar"];
test("robots and localized sitemap are public metadata routes", async () => {
  const robots = await fetch(`${base}/robots.txt`);
  assert.equal(robots.status, 200);
  assert.match(await robots.text(), /Sitemap: https?:\/\/[^\s]+\/sitemap.xml/);
  const response = await fetch(`${base}/sitemap.xml`);
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type"), /xml/);
  const xml = await response.text();
  assert.match(xml, /hreflang="zh-Hans"/);
  assert.match(xml, /hreflang="x-default"/);
  for (const locale of locales)
    assert.match(xml, new RegExp(`<loc>[^<]+/${locale}/contact</loc>`));
  assert.doesNotMatch(xml, /\/api\/v1\/|utm_|demo-/);
});
test("all locales expose social metadata, correct font links and no unconfigured analytics", async () => {
  for (const locale of locales) {
    const response = await fetch(`${base}/${locale}`);
    const html = await response.text();
    assert.equal(response.status, 200);
    assert.match(html, /<meta property="og:image" content="[^\"]+"/);
    assert.match(
      html,
      /<meta name="twitter:card" content="summary_large_image"/,
    );
    assert.match(html, /<link rel="icon"/);
    assert.doesNotMatch(
      html,
      /<script[^>]+src="https:\/\/www.googletagmanager/,
    );
    for (const font of ["ar", "zh"])
      assert.equal(html.includes(`/fonts/${font}.css`), locale === font);
  }
  const img = await fetch(`${base}/og-default.png`);
  assert.equal(img.status, 200);
  assert.match(img.headers.get("content-type"), /image\/png/);
});
