from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create standard WMS roles without creating sample users or records."

    def handle(self, *args, **options):
        for name in ["admin", "warehouse_manager", "warehouse_keeper", "accountant", "viewer"]:
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("WMS roles are ready."))
