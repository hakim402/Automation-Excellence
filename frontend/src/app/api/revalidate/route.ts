import { timingSafeEqual } from "node:crypto";
import { revalidatePath, revalidateTag } from "next/cache";
import { REVALIDATE_SECRET } from "@/lib/env";
export const runtime = "nodejs";
export async function POST(request: Request) {
  const reply = (body: object, status = 200) =>
    Response.json(body, { status, headers: { "Cache-Control": "no-store" } });
  if (!REVALIDATE_SECRET || REVALIDATE_SECRET.startsWith("replace-"))
    return reply({ error: "Not configured" }, 503);
  const supplied = Buffer.from(request.headers.get("authorization") ?? "");
  const expected = Buffer.from(`Bearer ${REVALIDATE_SECRET}`);
  if (
    supplied.length !== expected.length ||
    !timingSafeEqual(supplied, expected)
  )
    return reply({ error: "Unauthorized" }, 401);
  // One fixed scope avoids accepting arbitrary paths or cache tags from callers.
  const reader = request.body?.getReader();
  if (!reader) return reply({ error: "Invalid request" }, 400);
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > 1024) {
      await reader.cancel();
      return reply({ error: "Too large" }, 413);
    }
    chunks.push(value);
  }
  let body;
  try {
    body = JSON.parse(Buffer.concat(chunks).toString());
  } catch {
    return reply({ error: "Invalid JSON" }, 400);
  }
  if (!body || body.scope !== "content" || Object.keys(body).length !== 1)
    return reply({ error: "Invalid scope" }, 400);
  revalidateTag("public-content");
  revalidatePath("/[locale]", "layout");
  return reply({ revalidated: true });
}
