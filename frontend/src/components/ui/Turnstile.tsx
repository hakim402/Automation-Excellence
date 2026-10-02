"use client";
import Script from "next/script";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
type Widget = {
  render: (element: HTMLElement, options: Record<string, unknown>) => string;
  remove: (id: string) => void;
};
declare global {
  interface Window {
    turnstile?: Widget;
  }
}
export function Turnstile({
  locale,
  attempt,
  onToken,
}: {
  locale: string;
  attempt: number;
  onToken: (token: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const t = useTranslations("form");
  const sitekey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!ready || !ref.current || !window.turnstile || !sitekey) return;
    const id = window.turnstile.render(ref.current, {
      sitekey,
      action: "lead",
      language: locale === "zh" ? "zh-cn" : locale,
      theme: "auto",
      size: "flexible",
      "response-field": false,
      callback: (token: string) => {
        setFailed(false);
        onToken(token);
      },
      "expired-callback": () => onToken(""),
      "error-callback": () => {
        onToken("");
        setFailed(true);
      },
      "timeout-callback": () => onToken(""),
    });
    return () => {
      window.turnstile?.remove(id);
      onToken("");
    };
  }, [ready, sitekey, locale, attempt, onToken]);
  return (
    <div>
      {visible && (
        <Script
          src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
          onReady={() => setReady(true)}
          onError={() => setFailed(true)}
        />
      )}
      <div ref={ref} className="min-h-20" />
      {(!sitekey || failed) && (
        <p role="status" className="text-sm text-danger">
          {t("verificationUnavailable")}
        </p>
      )}
    </div>
  );
}
