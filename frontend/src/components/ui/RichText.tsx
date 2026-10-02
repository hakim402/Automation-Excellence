/** Accepts only the API's allowlisted, save-sanitized long-form fields. */
export function RichText({ html }: { html: string }) {
  return html ? (
    <div className="prose" dangerouslySetInnerHTML={{ __html: html }} />
  ) : null;
}
