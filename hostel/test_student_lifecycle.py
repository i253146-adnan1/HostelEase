from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance import services as finance_services
from hostel import room_service, student_service
from hostel.models import Room, RoomAssignment, Student

User = get_user_model()


class StudentLifecycleTests(TestCase):
    """Tests for VS-16: Student Left / Reactivation lifecycle (FR-13, BR-09, AC-13.1-13.3)."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden_vs16', password='WardenPassword123!', role='warden', is_staff=True
        )
        self.room = Room.objects.create(room_number='16-101', capacity=2)
        result = student_service.register_student(
            full_name='Bilal Raza',
            student_id='STU-1601',
            contact_number='03001234567',
            guardian_name='Raza',
            guardian_contact_number='03007654321',
            room_identifier='16-101',
            total_fee='30000',
            opening_paid='10000',
            temporary_password='StudentPass123!',
            created_by='warden_vs16',
        )
        self.student = result['student']
        self.student_user = result['user']
        self.student_user.must_change_password = False
        self.student_user.save(update_fields=['must_change_password'])

    def test_ac_13_1_mark_left_disables_login_clears_room_retains_records(self):
        self.client.force_login(self.warden)
        resp = self.client.post(
            reverse('hostel:warden_student_mark_left', args=[self.student.pk]),
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'marked Left')

        self.student.refresh_from_db()
        self.student_user.refresh_from_db()
        self.room.refresh_from_db()

        self.assertEqual(self.student.status, Student.STATUS_LEFT)
        self.assertFalse(self.student_user.is_active)
        self.assertIsNone(room_service.get_student_room('STU-1601'))
        self.assertEqual(self.room.occupancy, 0)
        # Historical assignment & fee ledger retained (BR-05, BR-09)
        self.assertEqual(RoomAssignment.objects.filter(student_id='STU-1601').count(), 1)
        self.assertEqual(finance_services.get_ledger(self.student.pk)['paid_amount'], Decimal('10000.00'))

    def test_ac_13_2_left_student_login_denied(self):
        student_service.mark_student_left(self.student.pk)
        login_resp = self.client.post(
            reverse('accounts:login'),
            {'username': 'STU-1601', 'password': 'StudentPass123!'},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_ac_13_3_reactivate_restores_login_same_record_and_empty_room(self):
        student_service.mark_student_left(self.student.pk)
        self.client.force_login(self.warden)
        resp = self.client.post(
            reverse('hostel:warden_student_reactivate', args=[self.student.pk]),
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'reactivated')

        self.student.refresh_from_db()
        self.student_user.refresh_from_db()
        self.assertEqual(self.student.status, Student.STATUS_ACTIVE)
        self.assertTrue(self.student_user.is_active)
        # Same record, no duplicate student ID
        self.assertEqual(Student.objects.filter(student_id='STU-1601').count(), 1)
        # Room remains empty until warden assigns a room (AC-13.3, OQ-15)
        self.assertIsNone(room_service.get_student_room('STU-1601'))
        self.assertContains(resp, 'No active room assignment')
        # Fee history still attached
        self.assertEqual(finance_services.get_ledger(self.student.pk)['remaining_amount'], Decimal('20000.00'))

        # Login works again
        self.client.post(reverse('accounts:logout'))
        login_resp = self.client.post(
            reverse('accounts:login'),
            {'username': 'STU-1601', 'password': 'StudentPass123!'},
            follow=True,
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertContains(login_resp, 'Student Portal')

    def test_invalid_lifecycle_transitions_rejected(self):
        with self.assertRaises(student_service.StudentValidationError):
            student_service.reactivate_student(self.student.pk)
        student_service.mark_student_left(self.student.pk)
        with self.assertRaises(student_service.StudentValidationError):
            student_service.mark_student_left(self.student.pk)

    def test_role_and_method_boundaries(self):
        mark_url = reverse('hostel:warden_student_mark_left', args=[self.student.pk])
        react_url = reverse('hostel:warden_student_reactivate', args=[self.student.pk])

        # Anonymous -> 302
        self.assertEqual(self.client.post(mark_url).status_code, 302)
        # Student -> 403
        self.client.force_login(self.student_user)
        self.assertEqual(self.client.post(mark_url).status_code, 403)
        self.assertEqual(self.client.post(react_url).status_code, 403)
        # Warden GET -> 405
        self.client.force_login(self.warden)
        self.assertEqual(self.client.get(mark_url).status_code, 405)
