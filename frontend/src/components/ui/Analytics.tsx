"use client";
import Script from "next/script";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { analyticsPage, validMeasurementId } from "@/lib/seo";

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}
/** Explicit pageviews cover App Router navigation without sending form/query data. */
export function Analytics({ measurementId }: { measurementId: string }) {
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const sent = useRef("");
  const valid = validMeasurementId(measurementId);
  useEffect(() => {
    if (!ready || !valid || !pathname || !window.gtag) return;
    const key = `${measurementId}:${pathname}`;
    if (sent.current === key) return;
    window.gtag("event", "page_view", {
      ...analyticsPage(window.location.origin, pathname),
      send_to: measurementId,
    });
    sent.current = key;
  }, [ready, valid, measurementId, pathname]);
  if (!valid) return null;
  return (
    <>
      <Script id="automex-analytics-config" strategy="afterInteractive">{`
      window.dataLayer = window.dataLayer || [];
      window.gtag = function(){window.dataLayer.push(arguments);};
      window.gtag('js', new Date());
      window.gtag('config', '${measurementId}', {send_page_view:false, allow_google_signals:false, allow_ad_personalization_signals:false});
    `}</Script>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
        strategy="afterInteractive"
        onReady={() => setReady(true)}
      />
    </>
  );
}
