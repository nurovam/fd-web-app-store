import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from store.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update the service account used for catalog management.'

    def handle(self, *args, **options):
        username = os.getenv('SERVICE_ACCOUNT_USERNAME', 'admin')
        email = os.getenv('SERVICE_ACCOUNT_EMAIL', '')
        password = os.getenv('SERVICE_ACCOUNT_PASSWORD', '')
        debug = os.getenv('DJANGO_DEBUG', '0') == '1'
        if not password:
            if debug:
                password = '12345678'
            else:
                raise CommandError('SERVICE_ACCOUNT_PASSWORD must be set in production.')
        if not debug and password in {'12345678', 'change-me', 'changeme'}:
            raise CommandError('SERVICE_ACCOUNT_PASSWORD must be a strong unique value in production.')

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.is_staff = True
        user.is_active = True
        user.set_password(password)
        user.save()
        Profile.objects.get_or_create(user=user)
        manager_group, _ = Group.objects.get_or_create(name='manager')
        user.groups.add(manager_group)

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} service account: {username}'))
