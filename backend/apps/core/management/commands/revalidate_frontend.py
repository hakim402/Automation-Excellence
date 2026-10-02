from django.core.management.base import BaseCommand, CommandError

from apps.core.revalidation import notify_frontend


class Command(BaseCommand):
    help = "Retry public frontend invalidation after a publish or deployment."

    def handle(self, *args, **options):
        if not notify_frontend():
            raise CommandError(
                "Revalidation unavailable. Check webhook configuration and frontend availability."
            )
        self.stdout.write(self.style.SUCCESS("Frontend content invalidated."))
