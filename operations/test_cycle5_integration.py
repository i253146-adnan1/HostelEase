from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from hostel import room_service
from hostel.models import Room, Student
from operations import leave_service
from operations.models import LeaveRequest

User = get_user_model()


class Cycle5IntegrationTests(TestCase):
    """Cross-module integration tests for Cycle 5 (VS-13, VS-14, VS-15) & dashboards."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden_c5', password='WardenPassword123!', role='warden', is_staff=True
        )
        self.student_user = User.objects.create_user(
            username='STU-C5-1', password='StudentPassword123!', role='student'
        )
        self.student = Student.objects.create(
            student_id='STU-C5-1',
            full_name='Tariq Mahmood',
            contact_number='03001234567',
            guardian_name='Mahmood',
            guardian_contact_number='03007654321',
            user_id=self.student_user.pk,
        )
        self.room = Room.objects.create(room_number='C5-101', capacity=2)
        room_service.assign_student(self.student.student_id, 'C5-101')

    def test_dashboards_expose_cycle5_links(self):
        self.client.force_login(self.warden)
        w_resp = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(w_resp, reverse('operations:warden_complaint_list'))
        self.assertContains(w_resp, reverse('operations:warden_leave_requests'))
        self.assertContains(w_resp, reverse('operations:warden_feedback_summary'))

        self.client.force_login(self.student_user)
        s_resp = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(s_resp, reverse('operations:complaint_list'))
        self.assertContains(s_resp, reverse('operations:student_leave_requests'))

    def test_leave_approval_preserves_student_status_room_and_login_br12(self):
        dep = date.today() + timedelta(days=2)
        ret = date.today() + timedelta(days=5)

        self.client.force_login(self.student_user)
        create_resp = self.client.post(
            reverse('operations:student_leave_request_create'),
            {'departure_date': dep.isoformat(), 'return_date': ret.isoformat(), 'reason': 'Family event'},
            follow=True,
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(len(leave_service.list_pending_leave_requests()), 1)

        leave_req = LeaveRequest.objects.get(student_id='STU-C5-1')
        self.client.force_login(self.warden)
        decide_resp = self.client.post(
            reverse('operations:warden_decide_leave_request', args=[leave_req.pk]),
            {'action': 'approve', 'warden_remark': 'Approved for 3 days'},
            follow=True,
        )
        self.assertEqual(decide_resp.status_code, 200)
        self.assertEqual(len(leave_service.list_pending_leave_requests()), 0)

        # BR-12: Active status, room assignment, and login access remain unchanged
        self.student.refresh_from_db()
        self.student_user.refresh_from_db()
        self.assertEqual(self.student.status, Student.STATUS_ACTIVE)
        self.assertTrue(self.student_user.is_active)
        self.assertEqual(room_service.get_student_room('STU-C5-1')['room_number'], 'C5-101')
