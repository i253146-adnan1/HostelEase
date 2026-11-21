from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance import services as finance_services
from hostel.models import Announcement, Room, Student

User = get_user_model()


class Cycle2EndToEndIntegrationTests(TestCase):
    """End-to-end integration test across Cycle 1 & Cycle 2 (VS-00..VS-04 + VS-06)."""

    def test_complete_cycle2_warden_and_student_workflow(self):
        # 1. Warden login
        warden = User.objects.create_user(
            username='warden_e2e',
            password='WardenPassword123!',
            role='warden',
            is_staff=True,
        )
        login_resp = self.client.post(
            reverse('accounts:login'),
            {'username': 'warden_e2e', 'password': 'WardenPassword123!'},
            follow=True,
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertContains(login_resp, 'Room Management')
        self.assertContains(login_resp, 'Student Management')
        self.assertContains(login_resp, 'Fees &amp; Payments')

        # 2. Warden creates a room (capacity = 1)
        room_resp = self.client.post(
            reverse('hostel:room_create'),
            {'room_number': 'E2E-101', 'capacity': 1},
            follow=True,
        )
        self.assertEqual(room_resp.status_code, 200)
        room = Room.objects.get(room_number='E2E-101')
        self.assertEqual(room.occupancy, 0)

        # 3. Warden registers a student assigned to E2E-101 with initial fee & opening balance
        reg_resp = self.client.post(
            reverse('hostel:warden_student_create'),
            {
                'full_name': 'Amina Tariq',
                'student_id': 'STU-E2E-1',
                'contact_number': '03001234567',
                'guardian_name': 'Tariq',
                'guardian_contact_number': '03007654321',
                'room': 'E2E-101',
                'total_fee': '25000',
                'opening_paid': '5000',
            },
        )
        self.assertEqual(reg_resp.status_code, 200)
        temp_password = reg_resp.context['temporary_password']
        student = Student.objects.get(student_id='STU-E2E-1')

        # 4. Check Room occupancy reflects the new assignment
        room.refresh_from_db()
        self.assertEqual(room.occupancy, 1)
        self.assertTrue(room.is_full)
        room_detail_resp = self.client.get(reverse('hostel:room_detail', args=[room.pk]))
        self.assertContains(room_detail_resp, 'STU-E2E-1')

        # 5. Check Fee Ledger shows student name, total, paid, and remaining
        ledger = finance_services.get_ledger(student.pk)
        self.assertEqual(ledger['total_fee'], Decimal('25000.00'))
        self.assertEqual(ledger['paid_amount'], Decimal('5000.00'))
        self.assertEqual(ledger['remaining_amount'], Decimal('20000.00'))
        fee_list_resp = self.client.get(reverse('finance:list'))
        self.assertContains(fee_list_resp, 'Amina Tariq')
        fee_detail_resp = self.client.get(reverse('finance:detail', args=[student.pk]))
        self.assertContains(fee_detail_resp, '20000.00')

        # Publish an announcement for the student to view
        Announcement.objects.create(title='Welcome Notice', message='Hostel opens at 8 AM.')

        # 6. Student logs in with temporary password -> forced password change -> dashboard & hostel info
        self.client.post(reverse('accounts:logout'))
        stu_login = self.client.post(
            reverse('accounts:login'),
            {'username': 'STU-E2E-1', 'password': temp_password},
            follow=True,
        )
        self.assertRedirects(stu_login, reverse('accounts:change_password'))

        pw_resp = self.client.post(
            reverse('accounts:change_password'),
            {
                'current_password': temp_password,
                'new_password': 'NewStudentPass123!',
                'confirm_password': 'NewStudentPass123!',
            },
            follow=True,
        )
        self.assertEqual(pw_resp.status_code, 200)
        self.assertContains(pw_resp, 'Student Portal')

        # Student views hostel info & is blocked from warden-only fee ledger
        ann_resp = self.client.get(reverse('hostel:student_announcements'))
        self.assertContains(ann_resp, 'Welcome Notice')
        self.assertEqual(self.client.get(reverse('finance:list')).status_code, 403)
