"""Explicit, bounded CLI equivalent of the admin translation action."""

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from apps.translations.client import TranslationError
from apps.translations.services import GroqTranslator, translated_fields


class Command(BaseCommand):
    help = "Translate missing fields of explicitly selected content records; never publishes."

    def add_arguments(self, parser):
        parser.add_argument("model", help="App label and model name, for example services.Service")
        parser.add_argument("ids", nargs="+", type=int)
        parser.add_argument(
            "--locale",
            action="append",
            dest="locales",
            help="Target locale; repeat as needed. Defaults to all five.",
        )

    def handle(self, *args, **options):
        try:
            model = apps.get_model(options["model"])
        except (LookupError, ValueError) as exc:
            raise CommandError("Unknown content model.") from exc
        if not translated_fields(model):
            raise CommandError("Only registered translatable content models are supported.")
        ids = set(options["ids"])
        objects = list(model.objects.filter(pk__in=ids))
        if len(objects) != len(ids):
            raise CommandError("One or more selected records do not exist.")
        translator = GroqTranslator()
        failed = 0
        for obj in objects:
            try:
                logs = translator.translate(obj, locales=options["locales"])
            except TranslationError as exc:
                raise CommandError(exc.code) from None
            for log in logs:
                self.stdout.write(
                    f"{model._meta.label} #{obj.pk} {log.locale}: "
                    f"{log.status} {log.error_code} (attempts={log.attempts})"
                )
                failed += log.status == "failed"
        if failed:
            raise CommandError(f"{failed} batch(es) failed. See Translation log; rerun to retry.")
