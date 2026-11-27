from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    """Create a warden user account."""

    help = 'Create a warden user with role=warden, is_staff=True, and is_superuser=False.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username for the warden account.')
        parser.add_argument('--password', required=True, help='Password for the warden account.')
        parser.add_argument('--email', default='', help='Email address for the warden account.')
        parser.add_argument('--mobile', default='', help='Mobile number for the warden account.')
        parser.add_argument('--name', default='', help='Full name for the warden account.')
        parser.add_argument('--main', action='store_true', help='Mark as Main Warden.')

    def handle(self, *args, **options):
        username = options['username'].strip()
        password = options['password']

        if not username:
            raise CommandError('Username cannot be empty.')

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists.')

        user = User.objects.create_user(
            username=username,
            password=password,
            role='warden',
            full_name=options['name'].strip(),
            email=options['email'].strip(),
            mobile_number=options['mobile'].strip(),
            is_main_warden=options['main'],
            is_staff=True,
            is_superuser=False,
        )
        self.stdout.write(self.style.SUCCESS(f'Warden user "{user.username}" created successfully.'))
