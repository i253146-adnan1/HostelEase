from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

MAIN_WARDEN_USERNAME = 'adnan'
MAIN_WARDEN_PASSWORD = 'adnan@1302'
MAIN_WARDEN_MOBILE = '03440734736'
MAIN_WARDEN_EMAIL = 'adnan0734736@gmail.com'
MAIN_WARDEN_NAME = 'Adnan'


class Command(BaseCommand):
    """Purge dummy/test user accounts (optional) and seed the Main Warden account."""

    help = 'Reset user accounts and seed the hardcoded Main Warden (adnan).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-reset',
            action='store_true',
            help='Skip purging existing user/student records and only ensure Main Warden exists.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['no_reset']:
            self._purge_accounts_and_related_records()

        user, created = User.objects.get_or_create(
            username=MAIN_WARDEN_USERNAME,
            defaults={
                'role': 'warden',
                'full_name': MAIN_WARDEN_NAME,
                'first_name': MAIN_WARDEN_NAME,
                'email': MAIN_WARDEN_EMAIL,
                'mobile_number': MAIN_WARDEN_MOBILE,
                'is_main_warden': True,
                'is_staff': True,
                'is_superuser': False,
                'must_change_password': False,
                'password_reset_expires_at': None,
            },
        )
        user.role = 'warden'
        user.full_name = MAIN_WARDEN_NAME
        user.first_name = MAIN_WARDEN_NAME
        user.email = MAIN_WARDEN_EMAIL
        user.mobile_number = MAIN_WARDEN_MOBILE
        user.is_main_warden = True
        user.is_staff = True
        user.is_superuser = False
        user.must_change_password = False
        user.password_reset_expires_at = None
        user.is_active = True
        user.set_password(MAIN_WARDEN_PASSWORD)
        user.save()

        action = 'created' if created else 'updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'Main Warden "{user.username}" {action} successfully (email={user.email}, mobile={user.mobile_number}).'
            )
        )

    def _purge_accounts_and_related_records(self):
        from accounts.models import StudentProfile
        from finance.models import FeeChange, FeeRecord, Payment
        from hostel.models import RoomAssignment, RoomRequest, RoomSwapNotification, Student
        from operations.models import (
            Complaint,
            Feedback,
            LeaveRequest,
            MealOptOut,
            StoredFile,
            VisitorLogEntry,
        )

        # Delete dependent records in FK-safe order
        RoomSwapNotification.objects.all().delete()
        RoomRequest.objects.all().delete()
        RoomAssignment.objects.all().delete()
        Payment.objects.all().delete()
        FeeChange.objects.all().delete()
        FeeRecord.objects.all().delete()
        Complaint.objects.all().delete()
        LeaveRequest.objects.all().delete()
        VisitorLogEntry.objects.all().delete()
        MealOptOut.objects.all().delete()
        Feedback.objects.all().delete()
        StoredFile.objects.all().delete()
        StudentProfile.objects.all().delete()
        Student.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write('Purged all existing user, student, and user-owned records.')
