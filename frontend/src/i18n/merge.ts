type Messages = { [key: string]: string | Messages };

/**
 * Deep-merges a locale's messages over English.
 *
 * A shallow spread would not do: if `ar.json` defines only one key inside a
 * `nav` object, a shallow merge replaces the whole English `nav` and every
 * other label in it renders blank. English must sit underneath every
 * individual string, at any depth (CLAUDE.md section 4).
 */
export function deepMerge(base: Messages, override: Messages): Messages {
  const out: Messages = { ...base };

  for (const [key, value] of Object.entries(override)) {
    const existing = out[key];

    if (isPlainObject(value) && isPlainObject(existing)) {
      out[key] = deepMerge(existing, value);
    } else if (value !== "" && value !== undefined && value !== null) {
      // An empty string is treated as "not translated yet" and keeps English.
      out[key] = value;
    }
  }

  return out;
}

function isPlainObject(value: unknown): value is Messages {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
