from datetime import datetime, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from hostel.models import Student
from hostel.student_service import StudentService
from .models import VisitorLogEntry
from .visitor_service import (
    VisitorLogError,
    create_visitor_entry,
    list_visitor_entries,
    record_check_out,
)

User = get_user_model()


class VisitorLogVS17Tests(TestCase):
    """Tests for VS-17 Warden Visitor Log (FR-18, BR-13, BR-05, NFR-01, EC-49, AC-18.1-18.4, OQ-32)."""

    @classmethod
    def setUpTestData(cls):
        cls.warden = User.objects.create_user(
            username='warden_vs17',
            password='Password123!',
            role='warden',
            is_staff=True,
        )
        cls.student_user = User.objects.create_user(
            username='STU-1701',
            password='Password123!',
            role='student',
            student_id='STU-1701',
        )
        cls.active_student = Student.objects.create(
            student_id='STU-1701',
            full_name='Ali Raza',
            contact_number='03001701001',
            guardian_name='Raza Ahmed',
            guardian_contact_number='03001701002',
            status=Student.STATUS_ACTIVE,
            user_id=cls.student_user.pk,
        )
        cls.left_student_user = User.objects.create_user(
            username='STU-1702',
            password='Password123!',
            role='student',
            student_id='STU-1702',
        )
        cls.left_student = Student.objects.create(
            student_id='STU-1702',
            full_name='Bilal Khan',
            contact_number='03001702001',
            guardian_name='Khan Sahib',
            guardian_contact_number='03001702002',
            status=Student.STATUS_LEFT,
            user_id=cls.left_student_user.pk,
        )

    def test_ac_18_1_valid_entry_saves_correctly(self):
        """AC-18.1: Valid entry referencing an existing student saves correctly."""
        check_in = datetime(2026, 11, 24, 10, 30, tzinfo=dt_timezone.utc)
        entry = create_visitor_entry(
            visitor_name='Tariq Mahmood',
            student_id='STU-1701',
            purpose='Family visit',
            check_in_time=check_in,
        )
        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.visitor_name, 'Tariq Mahmood')
        self.assertEqual(entry.student_id, 'STU-1701')
        self.assertEqual(entry.purpose, 'Family visit')
        self.assertEqual(entry.check_in_time, check_in)
        self.assertIsNone(entry.check_out_time)
        self.assertEqual(VisitorLogEntry.objects.count(), 1)

    def test_ac_18_2_ec_49_nonexistent_student_rejected(self):
        """AC-18.2 / EC-49: Non-existent student_id is rejected and nothing is saved."""
        check_in = datetime(2026, 11, 24, 11, 0, tzinfo=dt_timezone.utc)
        with self.assertRaises(VisitorLogError):
            create_visitor_entry(
                visitor_name='Unknown Visitor',
                student_id='STU-DOES-NOT-EXIST',
                purpose='Delivery',
                check_in_time=check_in,
            )
        self.assertEqual(VisitorLogEntry.objects.count(), 0)

    def test_log_28_existence_only_allows_left_student(self):
        """Log 28: Visitor entry validates student existence only, allowing Left students."""
        self.assertTrue(StudentService.student_exists('STU-1702'))
        self.assertIsNone(StudentService.validate_active_student('STU-1702'))

        check_in = datetime(2026, 11, 24, 12, 0, tzinfo=dt_timezone.utc)
        entry = create_visitor_entry(
            visitor_name='Former Roommate',
            student_id='STU-1702',
            purpose='Collect belongings',
            check_in_time=check_in,
        )
        self.assertEqual(entry.student_id, 'STU-1702')
        self.assertEqual(VisitorLogEntry.objects.count(), 1)

    def test_ac_18_3_record_checkout_and_reject_second_checkout(self):
        """AC-18.3: Check-out time updates an open entry; second check-out attempt is rejected."""
        check_in = datetime(2026, 11, 24, 9, 0, tzinfo=dt_timezone.utc)
        check_out = datetime(2026, 11, 24, 10, 15, tzinfo=dt_timezone.utc)
        second_check_out = datetime(2026, 11, 24, 11, 0, tzinfo=dt_timezone.utc)

        entry = create_visitor_entry(
            visitor_name='Salman Ali',
            student_id='STU-1701',
            purpose='Parent visit',
            check_in_time=check_in,
        )
        updated = record_check_out(entry.pk, check_out)
        self.assertEqual(updated.check_out_time, check_out)

        # Attempting to set check-out again must be rejected (no overwrite).
        with self.assertRaises(VisitorLogError):
            record_check_out(entry.pk, second_check_out)

        entry.refresh_from_db()
        self.assertEqual(entry.check_out_time, check_out)

    def test_record_checkout_rejects_time_before_checkin(self):
        """Check-out time earlier than check-in time is rejected."""
        check_in = datetime(2026, 11, 24, 14, 0, tzinfo=dt_timezone.utc)
        earlier = datetime(2026, 11, 24, 13, 30, tzinfo=dt_timezone.utc)
        entry = create_visitor_entry(
            visitor_name='Nadia Bibi',
            student_id='STU-1701',
            purpose='Document drop-off',
            check_in_time=check_in,
        )
        with self.assertRaises(VisitorLogError):
            record_check_out(entry.pk, earlier)

        entry.refresh_from_db()
        self.assertIsNone(entry.check_out_time)

    def test_br_05_oq_32_delete_raises_permission_error(self):
        """BR-05 / OQ-32: VisitorLogEntry.delete() raises PermissionError."""
        entry = create_visitor_entry(
            visitor_name='Retained Visitor',
            student_id='STU-1701',
            purpose='Meeting',
            check_in_time=datetime(2026, 11, 24, 15, 0, tzinfo=dt_timezone.utc),
        )
        with self.assertRaises(PermissionError):
            entry.delete()
        self.assertEqual(VisitorLogEntry.objects.count(), 1)

    def test_ac_18_4_br_13_nfr_01_student_direct_url_access_denied(self):
        """AC-18.4 / BR-13 / NFR-01: Logged-in student is denied (403) on all visitor-log URLs."""
        entry = create_visitor_entry(
            visitor_name='Confidential Visitor',
            student_id='STU-1701',
            purpose='Private visit',
            check_in_time=datetime(2026, 11, 24, 16, 0, tzinfo=dt_timezone.utc),
        )
        client = Client()
        client.force_login(self.student_user)

        list_url = reverse('operations:warden_visitor_log')
        create_url = reverse('operations:warden_visitor_create')
        checkout_url = reverse('operations:warden_visitor_checkout', args=[entry.pk])

        self.assertEqual(client.get(list_url).status_code, 403)
        self.assertEqual(client.get(create_url).status_code, 403)
        self.assertEqual(
            client.post(
                create_url,
                {
                    'visitor_name': 'Sneaky',
                    'student_id': 'STU-1701',
                    'purpose': 'Test',
                    'check_in_time': '2026-11-24T17:00',
                },
            ).status_code,
            403,
        )
        self.assertEqual(client.get(checkout_url).status_code, 403)
        self.assertEqual(
            client.post(checkout_url, {'check_out_time': '2026-11-24T18:00'}).status_code,
            403,
        )

        # Student dashboard must not contain any visitor-log link.
        dashboard_resp = client.get(reverse('accounts:dashboard'))
        self.assertEqual(dashboard_resp.status_code, 200)
        self.assertNotContains(dashboard_resp, list_url)

    def test_anonymous_user_redirected_to_login(self):
        """NFR-01: Anonymous users are redirected to login on all visitor-log URLs."""
        entry = create_visitor_entry(
            visitor_name='Guest',
            student_id='STU-1701',
            purpose='Inquiry',
            check_in_time=datetime(2026, 11, 24, 10, 0, tzinfo=dt_timezone.utc),
        )
        client = Client()
        for url in [
            reverse('operations:warden_visitor_log'),
            reverse('operations:warden_visitor_create'),
            reverse('operations:warden_visitor_checkout', args=[entry.pk]),
        ]:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/accounts/login/', resp['Location'])

    def test_warden_views_list_create_and_checkout_end_to_end(self):
        """Warden can view Visitor Log, create an entry, reject unknown student, and record check-out."""
        client = Client()
        client.force_login(self.warden)

        list_url = reverse('operations:warden_visitor_log')
        create_url = reverse('operations:warden_visitor_create')

        # List view renders 200.
        resp = client.get(list_url)
        self.assertEqual(resp.status_code, 200)

        # Create valid entry via POST.
        resp = client.post(
            create_url,
            {
                'visitor_name': 'Imran Qureshi',
                'student_id': 'STU-1701',
                'purpose': 'Books delivery',
                'check_in_time': '2026-11-24T10:00',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(VisitorLogEntry.objects.count(), 1)
        entry = list_visitor_entries().first()
        self.assertEqual(entry.visitor_name, 'Imran Qureshi')

        # Reject non-existent student via POST.
        resp = client.post(
            create_url,
            {
                'visitor_name': 'Ghost Visitor',
                'student_id': 'STU-9999',
                'purpose': 'Unknown',
                'check_in_time': '2026-11-24T11:00',
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No student record found')
        self.assertEqual(VisitorLogEntry.objects.count(), 1)

        # Record check-out via POST.
        checkout_url = reverse('operations:warden_visitor_checkout', args=[entry.pk])
        resp = client.post(checkout_url, {'check_out_time': '2026-11-24T11:30'})
        self.assertEqual(resp.status_code, 302)
        entry.refresh_from_db()
        self.assertIsNotNone(entry.check_out_time)
