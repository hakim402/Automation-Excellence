"use client";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { usePathname } from "@/i18n/navigation";
import type { ServiceSummary } from "@/lib/api-types";
import { captureLead, CaptureError } from "@/lib/capture";
import { Button } from "@/components/ui/Button";
import { Turnstile } from "@/components/ui/Turnstile";
export function QuoteForm({
  services,
  service = "",
  product = "",
}: {
  services: ServiceSummary[];
  service?: string;
  product?: string;
}) {
  const t = useTranslations("form");
  const locale = useLocale();
  const pathname = usePathname();
  const id = useId();
  const [token, setToken] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [pending, setPending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [fields, setFields] = useState<string[]>([]);
  const [contact, setContact] = useState("email");
  const status = useRef<HTMLParagraphElement>(null);
  const onToken = useCallback((value: string) => setToken(value), []);
  useEffect(() => {
    if (success) status.current?.focus();
  }, [success]);
  if (success)
    return (
      <p
        tabIndex={-1}
        ref={status}
        role="status"
        className="border-s-2 border-success bg-surface p-6 text-lg"
      >
        {t("success")}
      </p>
    );
  return (
    <form
      className="ax-form max-w-3xl"
      onSubmit={async (event) => {
        event.preventDefault();
        if (pending || !token) return;
        const form = event.currentTarget;
        const data = new FormData(form);
        const payload: Record<string, string> = {};
        for (const [key, value] of data)
          if (typeof value === "string" && (value || key === "website"))
            payload[key] = value;
        payload.locale = locale;
        payload.source_path = `/${locale}${pathname === "/" ? "" : pathname}`;
        payload.turnstile_token = token;
        if (product) payload.product = product;
        const query = new URLSearchParams(window.location.search);
        for (const key of ["utm_source", "utm_medium", "utm_campaign"]) {
          const value = query.get(key);
          if (value) payload[key] = value.slice(0, 200);
        }
        setPending(true);
        setError("");
        setFields([]);
        try {
          await captureLead(payload);
          setSuccess(true);
        } catch (err) {
          const failure =
            err instanceof CaptureError ? err : new CaptureError(0);
          setFields(failure.fields);
          setError(
            failure.status === 429
              ? t("rateLimited")
              : failure.status === 400
                ? t("invalid")
                : failure.status === 0
                  ? t("network")
                  : t("unavailable"),
          );
          requestAnimationFrame(() => status.current?.focus());
        } finally {
          setPending(false);
          setToken("");
          setAttempt((value) => value + 1);
        }
      }}
    >
      <p className="mb-6 text-sm text-text-mute">{t("required")}</p>
      <div className="grid gap-6 sm:grid-cols-2">
        {(
          [
            ["full_name", "text", 160],
            ["email", "email", 254],
            ["company", "text", 160],
            ["country", "text", 100],
          ] as const
        ).map(([name, type, max]) => (
          <label key={name} htmlFor={`${id}-${name}`}>
            <span>
              {t(name)}
              {["full_name", "email"].includes(name) ? " *" : ""}
            </span>
            <input
              id={`${id}-${name}`}
              name={name}
              type={type}
              required={["full_name", "email"].includes(name)}
              maxLength={max}
              autoComplete={
                name === "full_name"
                  ? "name"
                  : name === "company"
                    ? "organization"
                    : name === "country"
                      ? "country-name"
                      : "email"
              }
              aria-invalid={fields.includes(name)}
            />
          </label>
        ))}
        <label htmlFor={`${id}-preferred_contact`}>
          {t("preferred_contact")}
          <select
            id={`${id}-preferred_contact`}
            name="preferred_contact"
            value={contact}
            onChange={(event) => setContact(event.target.value)}
          >
            {["email", "phone", "whatsapp"].map((value) => (
              <option key={value} value={value}>
                {t(value)}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor={`${id}-phone`}>
          {t("phone")}
          {contact !== "email" ? " *" : ""}
          <input
            id={`${id}-phone`}
            name="phone"
            type="tel"
            autoComplete="tel"
            maxLength={40}
            required={contact !== "email"}
            aria-invalid={fields.includes("phone")}
          />
        </label>
      </div>
      <label className="mt-6 block" htmlFor={`${id}-service`}>
        {t("service")}
        <select id={`${id}-service`} name="service" defaultValue={service}>
          <option value="">{t("chooseService")}</option>
          {services.map((item) => (
            <option key={item.slug} value={item.slug}>
              {item.name}
            </option>
          ))}
        </select>
      </label>
      <label className="mt-6 block" htmlFor={`${id}-message`}>
        {t("message")} *
        <textarea
          id={`${id}-message`}
          name="message"
          rows={6}
          required
          maxLength={10000}
          aria-invalid={fields.includes("message")}
        />
      </label>
      <div hidden aria-hidden="true">
        <label htmlFor={`${id}-website`}>
          Website
          <input
            id={`${id}-website`}
            name="website"
            tabIndex={-1}
            autoComplete="off"
          />
        </label>
      </div>
      <p className="my-6 text-sm text-text-mute">{t("privacy")}</p>
      <Turnstile locale={locale} attempt={attempt} onToken={onToken} />
      {error && (
        <p ref={status} tabIndex={-1} role="alert" className="my-5 text-danger">
          {error}
        </p>
      )}
      <Button type="submit" disabled={pending || !token} className="mt-5">
        {pending ? t("sending") : t("submit")}
      </Button>
      <noscript>
        <p>{t("javascript")}</p>
      </noscript>
    </form>
  );
}
