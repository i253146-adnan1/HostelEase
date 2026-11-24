from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from finance import services as finance_services
from hostel import student_service
from hostel.models import Room
from operations import leave_service, meal_service
from operations.complaint_service import ComplaintService

User = get_user_model()


class StudentHomeVS20Tests(TestCase):
    """Tests for VS-20: Consolidated student home, own-record isolation, and empty states."""

    def setUp(self):
        self.room = Room.objects.create(room_number='20-101', capacity=2)
        res1 = student_service.register_student(
            full_name='Sana Tariq',
            student_id='STU-2001',
            contact_number='03001234567',
            guardian_name='Tariq',
            guardian_contact_number='03007654321',
            room_identifier='20-101',
            total_fee='40000',
            opening_paid='15000',
            temporary_password='StudentPass123!',
            created_by='warden',
        )
        self.s1 = res1['student']
        self.u1 = res1['user']
        self.u1.must_change_password = False
        self.u1.save(update_fields=['must_change_password'])

        res2 = student_service.register_student(
            full_name='Hina Ali',
            student_id='STU-2002',
            contact_number='03011234567',
            guardian_name='Ali',
            guardian_contact_number='03017654321',
            room_identifier='20-101',
            total_fee='10000',
            opening_paid='10000',
            temporary_password='StudentPass123!',
            created_by='warden',
        )
        self.s2 = res2['student']
        self.u2 = res2['user']
        self.u2.must_change_password = False
        self.u2.save(update_fields=['must_change_password'])

    def test_student_home_shows_own_consolidated_summary_and_all_links(self):
        today = timezone.localdate()
        ComplaintService.submit_complaint(
            student_user=self.u1, category='internet', description='Slow Wi-Fi in room'
        )
        leave_service.submit_leave_request(
            student_id='STU-2001',
            departure_date=today + timedelta(days=2),
            return_date=today + timedelta(days=4),
            reason='Home visit',
        )
        meal_service.create_opt_out(
            student_id='STU-2001', meal_date=today + timedelta(days=2), meal_type='Dinner'
        )
        finance_services.add_payment(self.s1.pk, '5000', status='Pending')

        self.client.force_login(self.u1)
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Sana Tariq')
        self.assertContains(resp, '20-101')
        self.assertContains(resp, '25000.00')  # remaining fee = 40000 - 15000
        self.assertContains(resp, '1 proof(s)')
        self.assertContains(resp, 'Leave: Pending')
        self.assertContains(resp, 'Active Meal Opt-Outs: 1')

        # Navigation links to all implemented student features
        for name in (
            'finance_student:my_fees',
            'operations:complaint_list',
            'hostel:student_room_requests',
            'hostel:student_swap_inbox',
            'operations:student_leave_requests',
            'hostel:student_announcements',
            'hostel:student_menu',
            'hostel:student_rules',
            'operations:student_meal_optouts',
            'operations:student_feedback',
        ):
            self.assertContains(resp, reverse(name))

        # No warden-only visitor log exposed
        self.assertNotContains(resp, reverse('operations:warden_visitor_log'))

    def test_two_student_isolation_and_no_cross_student_data(self):
        ComplaintService.submit_complaint(
            student_user=self.u1, category='internet', description='Secret complaint S1'
        )
        self.client.force_login(self.u2)
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Hina Ali')
        self.assertNotContains(resp, 'Sana Tariq')
        self.assertNotContains(resp, '25000.00')
        self.assertContains(resp, '0 proof(s)')
        self.assertContains(resp, 'Leave: None')
        # Student 2 cannot open warden visitor log or fee management
        self.assertEqual(self.client.get(reverse('operations:warden_visitor_log')).status_code, 403)
        self.assertEqual(self.client.get(reverse('finance:list')).status_code, 403)

    def test_empty_state_without_profile_renders_cleanly(self):
        bare_student = User.objects.create_user(
            username='bare_stu', password='StudentPassword123!', role='student'
        )
        self.client.force_login(bare_student)
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Your student profile has not been set up yet')
