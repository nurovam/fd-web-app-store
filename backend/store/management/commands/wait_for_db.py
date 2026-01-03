import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Wait for database to be available.'

    def handle(self, *args, **options):
        db_conn = None
        retries = 30
        while retries > 0:
            try:
                db_conn = connections['default']
                db_conn.ensure_connection()
                self.stdout.write(self.style.SUCCESS('Database available.'))
                return
            except OperationalError:
                retries -= 1
                time.sleep(1)
        self.stdout.write(self.style.ERROR('Database unavailable.'))
        raise OperationalError
