# Self-hosted locale fonts

IBM Plex Sans Arabic (400/600) and Noto Sans SC (400/700), downloaded by next/font from Google Fonts during the Phase 6 build and vendored for locale-conditional loading. The generated unicode-range subsets retain complete language coverage and measured fallback metrics. Font licenses are included beside these files.

Only `/ar` links `ar.css`; only `/zh` links `zh.css`. CSS and binaries are served locally. Latin and monospace faces remain managed by next/font. These hashed font files are immutable; regenerate filenames when replacing a font. Keep the full unicode ranges rather than subsetting to current UI strings, because editors can add new content.

Sources: https://github.com/google/fonts/tree/main/ofl/ibmplexsansarabic and https://github.com/google/fonts/tree/main/ofl/notosanssc.
