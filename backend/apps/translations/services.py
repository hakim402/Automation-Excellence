"""Translate missing columns, validate the batch, then save with a fresh row lock."""

import logging
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from modeltranslation.translator import NotRegistered, translator

from apps.core.models import Publishable, TranslationTracked

from .client import GroqClient, TranslationError
from .models import TranslationLog
from .validation import validate_translation

logger = logging.getLogger(__name__)


def translated_fields(model):
    if not issubclass(model, TranslationTracked):
        return ()
    try:
        names = translator.get_options_for_model(model._meta.concrete_model).fields
    except NotRegistered:
        return ()
    return tuple(field.name for field in model._meta.fields if field.name in names)


class GroqTranslator:
    def __init__(self, *, client=None, actor=None, run_id=None):
        self.client = client
        self.actor = actor
        self.run_id = run_id or uuid.uuid4()

    def _log(self, obj, locale, fields, status, code="", attempts=0):
        entry = TranslationLog.objects.create(
            run_id=self.run_id,
            content_type=ContentType.objects.get_for_model(obj, for_concrete_model=False),
            object_id=str(obj.pk),
            locale=locale,
            fields=list(fields),
            status=status,
            error_code=code,
            attempts=attempts,
            model_name=settings.GROQ_MODEL,
            actor=self.actor,
        )
        if status == "failed":
            logger.warning("Translation failed log_id=%s code=%s", entry.pk, code)
        return entry

    def translate(self, obj, *, locales=None):
        if not obj.pk or not translated_fields(type(obj)):
            raise TranslationError("unsupported_record")
        allowed = {code for code, _ in settings.LANGUAGES if code != "en"}
        locales = (
            tuple(locales)
            if locales is not None
            else tuple(code for code, _ in settings.LANGUAGES if code != "en")
        )
        if not locales or len(set(locales)) != len(locales) or not set(locales) <= allowed:
            raise TranslationError("unsupported_locale")
        results = []
        for locale in locales:
            try:
                snapshot = type(obj).objects.get(pk=obj.pk)
            except type(obj).DoesNotExist:
                results.append(self._log(obj, locale, [], "skipped", "record_deleted"))
                continue
            fields = {}
            for name in translated_fields(type(obj)):
                source = snapshot.__dict__.get(f"{name}_en")
                target = snapshot.__dict__.get(f"{name}_{locale}")
                if source and source.strip() and not (target and target.strip()):
                    fields[name] = {
                        "text": source,
                        "max_length": obj._meta.get_field(name).max_length,
                    }
            if not fields:
                results.append(self._log(obj, locale, [], "skipped", "nothing_missing"))
                continue
            terms = {"Automex"}
            for name in ("name", "company_name", "client_name", "client_company"):
                if name not in translated_fields(type(obj)) and snapshot.__dict__.get(name):
                    terms.add(snapshot.__dict__[name])
            batch, size = {}, 0
            for name, field in fields.items():
                length = len(field["text"])
                if length > settings.GROQ_BATCH_CHARS:
                    results.append(self._log(obj, locale, [name], "failed", "source_too_long"))
                    continue
                if batch and size + length > settings.GROQ_BATCH_CHARS:
                    results.extend(self._translate_batch(snapshot, locale, batch, sorted(terms)))
                    batch, size = {}, 0
                batch[name] = field
                size += length
            if batch:
                results.extend(self._translate_batch(snapshot, locale, batch, sorted(terms)))
        return results

    def _translate_batch(self, snapshot, locale, batch, terms):
        attempts = 0
        try:
            if self.client is None:
                self.client = GroqClient()
            output, attempts = self.client.translate(batch, locale, terms)
            if not isinstance(output, dict) or set(output) != set(batch):
                raise TranslationError("field_mismatch")
            validated = {}
            for name, field in batch.items():
                validated[name] = validate_translation(
                    field["text"],
                    output[name],
                    max_length=field["max_length"],
                    rich=name in getattr(snapshot, "rich_text_fields", ()),
                    profile=getattr(snapshot, "rich_text_profiles", {}).get(name, "default"),
                    terms=terms,
                )
        except TranslationError as exc:
            return [
                self._log(snapshot, locale, batch, "failed", exc.code, max(attempts, exc.attempts))
            ]
        # Network calls never hold a row lock. Recheck raw columns under the lock so a
        # human edit or another translation that finished first cannot be overwritten.
        with transaction.atomic():
            current = type(snapshot).objects.select_for_update().filter(pk=snapshot.pk).first()
            if current is None:
                return [self._log(snapshot, locale, batch, "skipped", "record_deleted", attempts)]
            changes, skipped = {}, []
            for name, value in validated.items():
                target = current.__dict__.get(f"{name}_{locale}")
                if current.__dict__.get(f"{name}_en") != batch[name]["text"] or (
                    target and target.strip()
                ):
                    skipped.append(name)
                else:
                    changes[f"{name}_{locale}"] = value
            logs = []
            if changes:
                for name, value in changes.items():
                    setattr(current, name, value)
                current.translation_status = "machine"
                update_fields = {*changes, "translation_status"}
                if isinstance(current, Publishable):
                    current.status = "draft"
                    update_fields.add("status")
                if hasattr(current, "updated_at"):
                    current.updated_at = timezone.now()
                    update_fields.add("updated_at")
                current.save(update_fields=update_fields)
                logs.append(
                    self._log(
                        snapshot,
                        locale,
                        [name for name in batch if name not in skipped],
                        "success",
                        attempts=attempts,
                    )
                )
            if skipped:
                logs.append(
                    self._log(snapshot, locale, skipped, "skipped", "record_changed", attempts)
                )
            return logs
