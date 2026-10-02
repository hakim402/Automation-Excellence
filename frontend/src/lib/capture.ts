/** The only browser-to-Django write transport. Never imports server environment values. */
export class CaptureError extends Error {
  constructor(
    readonly status: number,
    readonly fields: string[] = [],
    readonly retryAfter?: string,
  ) {
    super("Capture request failed");
  }
}
export async function captureLead(payload: Record<string, string>) {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) throw new CaptureError(503);
  const response = await fetch(`${base.replace(/\/$/, "")}/crm/leads/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
    credentials: "omit",
    cache: "no-store",
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new CaptureError(
      response.status,
      Object.keys(body),
      response.headers.get("Retry-After") ?? undefined,
    );
  }
  if (response.status !== 201) throw new CaptureError(502);
}
