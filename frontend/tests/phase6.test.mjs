import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import ts from "typescript";
function load(file, imports = {}, fetchImpl = fetch, env = {}) {
  const source = fs.readFileSync(
    path.join(import.meta.dirname, "../src", file),
    "utf8",
  );
  const code = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  const exports = {};
  new Function("require", "exports", "fetch", "process", code)(
    (name) => {
      if (name in imports) return imports[name];
      throw Error(name);
    },
    exports,
    fetchImpl,
    { env },
  );
  return exports;
}
test("revalidation rejects wrong credentials and invalid scopes; fixed scope clears content and layout", async () => {
  const calls = [];
  const api = load("app/api/revalidate/route.ts", {
    "node:crypto": crypto,
    "next/cache": {
      revalidateTag: (tag) => calls.push(tag),
      revalidatePath: (...args) => calls.push(args),
    },
    "@/lib/env": { REVALIDATE_SECRET: "fixture-only-secret" },
  });
  const request = (body, auth = "Bearer fixture-only-secret") =>
    new Request("http://localhost/api/revalidate", {
      method: "POST",
      headers: { authorization: auth },
      body,
    });
  assert.equal(
    (await api.POST(request('{"scope":"content"}', "Bearer wrong"))).status,
    401,
  );
  assert.equal(
    (await api.POST(request('{"scope":"content","path":"/admin"}'))).status,
    400,
  );
  assert.equal((await api.POST(request("invalid"))).status, 400);
  assert.equal((await api.POST(request("x".repeat(1025)))).status, 413);
  assert.deepEqual(calls, []);
  const result = await api.POST(request('{"scope":"content"}'));
  assert.equal(result.status, 200);
  assert.equal(result.headers.get("cache-control"), "no-store");
  assert.deepEqual(calls, ["public-content", ["/[locale]", "layout"]]);
});
test("revalidation fails closed for missing configuration", async () => {
  const api = load("app/api/revalidate/route.ts", {
    "node:crypto": crypto,
    "next/cache": {},
    "@/lib/env": { REVALIDATE_SECRET: "" },
  });
  assert.equal(
    (await api.POST(new Request("http://localhost", { method: "POST" })))
      .status,
    503,
  );
});
test("lead transport uses only public URL and returns structured safe failures", async () => {
  let sent;
  const api = load(
    "lib/capture.ts",
    {},
    async (url, options) => {
      sent = { url, options };
      return Response.json({ detail: "received" }, { status: 201 });
    },
    { NEXT_PUBLIC_API_URL: "https://api.example.test/api/v1" },
  );
  await api.captureLead({
    full_name: "Fixture",
    turnstile_token: "test-token",
  });
  assert.equal(sent.url, "https://api.example.test/api/v1/crm/leads/");
  assert.equal(sent.options.credentials, "omit");
  assert.equal(sent.options.cache, "no-store");
  assert.ok(sent.options.signal);
  const denied = load(
    "lib/capture.ts",
    {},
    async () =>
      Response.json(
        { turnstile_token: "expired" },
        { status: 429, headers: { "Retry-After": "42" } },
      ),
    { NEXT_PUBLIC_API_URL: "https://api.example.test/api/v1" },
  );
  await assert.rejects(
    denied.captureLead({}),
    (error) => error.status === 429 && error.retryAfter === "42",
  );
});
test("video embeds accept only exact provider hosts and validated IDs", () => {
  const { videoEmbed } = load("lib/video.ts");
  assert.equal(
    videoEmbed({
      source: "youtube",
      external_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }),
    "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?cc_load_policy=1",
  );
  assert.equal(
    videoEmbed({ source: "vimeo", external_url: "https://vimeo.com/123456" }),
    "https://player.vimeo.com/video/123456",
  );
  for (const external_url of [
    "javascript:alert(1)",
    "https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ",
    "https://youtube.com/watch?v=invalid",
    "http://youtube.com/watch?v=dQw4w9WgXcQ",
  ])
    assert.equal(videoEmbed({ source: "youtube", external_url }), null);
});
