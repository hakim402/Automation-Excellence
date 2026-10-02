import { dirname } from "path";
import { fileURLToPath } from "url";

import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: dirname(fileURLToPath(import.meta.url)) });

/**
 * Next 15 ships its shareable configs in eslintrc format, so FlatCompat
 * bridges them into ESLint 9's flat config.
 *
 * The restricted-syntax rules below turn two of CLAUDE.md's rules into build
 * failures rather than things a reviewer has to remember:
 *   - section 7: physical direction utilities break the Arabic layout, and
 *     most RTL bugs are invisible when you are looking at English.
 *   - section 8: tokens.css is the single source of truth for colour.
 */
const DIRECTIONAL_UTILITIES =
  "/(^|\\s|:)-?(ml|mr|pl|pr)-|(^|\\s|:)(left|right)-|(^|\\s|:)text-(left|right)(\\s|$)|(^|\\s|:)(border|rounded)-(l|r)(-|\\s|$)/";

const HEX_COLOUR = "/#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\\b/";

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", ".next-dev/**", "out/**", "build/**", "next-env.d.ts", "node_modules/**"],
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: `JSXAttribute[name.name='className'] Literal[value=${DIRECTIONAL_UTILITIES}]`,
          message:
            "Use CSS logical properties (ms/me, ps/pe, start/end, text-start/text-end, border-s/border-e). Physical direction utilities do not mirror in Arabic. See CLAUDE.md section 7.",
        },
        {
          selector: `JSXAttribute[name.name='className'] TemplateElement[value.raw=${DIRECTIONAL_UTILITIES}]`,
          message:
            "Use CSS logical properties (ms/me, ps/pe, start/end, text-start/text-end, border-s/border-e). Physical direction utilities do not mirror in Arabic. See CLAUDE.md section 7.",
        },
        {
          selector: `JSXAttribute[name.name=/^(className|style)$/] Literal[value=${HEX_COLOUR}]`,
          message:
            "Hard-coded colours are a bug. Use a token from src/styles/tokens.css. See CLAUDE.md section 8.",
        },
      ],
    },
  },
];

export default eslintConfig;
