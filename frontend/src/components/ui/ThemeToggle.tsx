"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

const subscribe = () => () => {};

export function ThemeToggle() {
  const t = useTranslations("theme");
  const { theme, setTheme } = useTheme();
  // The server cannot read localStorage. Keep the initial control stable,
  // then reflect the stored choice once React hydrates it.
  const mounted = useSyncExternalStore(subscribe, () => true, () => false);

  return (
    <label className="flex items-center gap-3 text-sm text-text-2 print:hidden">
      {t("label")}
      <select
        value={mounted ? theme ?? "system" : "system"}
        onChange={(event) => setTheme(event.target.value)}
        disabled={!mounted}
        className="min-h-11 rounded-sm border border-border bg-surface px-3 py-2 text-text"
      >
        {(["light", "dark", "system"] as const).map((value) => (
          <option key={value} value={value}>{t(value)}</option>
        ))}
      </select>
    </label>
  );
}
