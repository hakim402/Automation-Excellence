// Code-native brand card. Run after changing the semantic dark theme tokens.
import fs from "node:fs/promises";
import sharp from "sharp";
import { fileURLToPath } from "node:url";
const css = await fs.readFile(
  new URL("../src/styles/tokens.css", import.meta.url),
  "utf8",
);
const base = css.split('[data-theme="dark"]')[0];
const dark = css.split('[data-theme="dark"]')[1].split("}")[0];
const resolve = (name) => {
  const rule = new RegExp(`${name}:\\s*([^;]+);`);
  const value = (dark.match(rule) || base.match(rule))?.[1].trim();
  if (!value) throw new Error(`Missing token ${name}`);
  return value.startsWith("var(") ? resolve(value.slice(4, -1)) : value;
};
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="1200" height="630" fill="${resolve("--bg")}"/><path d="M80 120H1120M80 510H1120" stroke="${resolve("--border")}" stroke-width="2"/><text x="80" y="345" font-family="Arial,sans-serif" font-size="128" font-weight="700" fill="${resolve("--text")}">Automex<tspan fill="${resolve("--accent")}">.</tspan></text><text x="84" y="433" font-family="Arial,sans-serif" font-size="32" fill="${resolve("--text-2")}">automex.tech</text></svg>`;
await sharp(Buffer.from(svg))
  .png()
  .toFile(fileURLToPath(new URL("../public/og-default.png", import.meta.url)));

const icon = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="${resolve("--bg")}"/><text x="9" y="49" font-family="Arial,sans-serif" font-size="50" font-weight="700" fill="${resolve("--text")}">A</text><rect x="48" y="46" width="8" height="8" fill="${resolve("--accent")}"/></svg>`;
await sharp(Buffer.from(icon))
  .png()
  .toFile(fileURLToPath(new URL("../public/favicon.png", import.meta.url)));
