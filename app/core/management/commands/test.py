from django.core.management.commands.test import Command as BaseCommand


class Command(BaseCommand):
    def handle(self, *test_labels, **options):
        # Wrap Django's built-in test command to always delete the database if
        # it exists
        options["interactive"] = False
        return super().handle(*test_labels, **options)
