import time
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from dashboard.services import get_warden_pending_summary
from finance import services as finance_services
from finance.models import Payment
from hostel import room_service, services as hostel_services
from hostel.models import RoomRequest, Student
from operations.complaint_service import ComplaintService

User = get_user_model()


class WardenDashboardVS19Tests(TestCase):
    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden_dash',
            password='WardenPassword123',
            role='warden',
            is_staff=True,
        )
        self.student1 = User.objects.create_user(
            username='stu_dash_1',
            password='StudentPassword123',
            role='student',
            student_id='STU-D01',
        )
        self.student2 = User.objects.create_user(
            username='stu_dash_2',
            password='StudentPassword123',
            role='student',
            student_id='STU-D02',
        )
        self.student3 = User.objects.create_user(
            username='stu_dash_3',
            password='StudentPassword123',
            role='student',
            student_id='STU-D03',
        )

    def test_dashboard_owns_no_database_tables(self):
        """ADR-005 / AGENTS.md: Dashboard must not own any database models or tables."""
        dashboard_models = list(apps.get_app_config('dashboard').get_models())
        self.assertEqual(dashboard_models, [])

    def test_zero_count_state(self):
        """VS-19: Empty state renders all four counts as 0 without errors."""
        self.client.force_login(self.warden)
        response = self.client.get(reverse('dashboard:warden_dashboard'))
        self.assertEqual(response.status_code, 200)
        summary = response.context['pending_summary']
        self.assertEqual(summary['pending_payment_proofs'], 0)
        self.assertEqual(summary['pending_complaints'], 0)
        self.assertEqual(summary['pending_room_requests'], 0)
        self.assertEqual(summary['pending_leave_requests'], 0)
        self.assertEqual(summary['total_pending'], 0)
        self.assertContains(response, 'Pending Payment Proofs')
        self.assertContains(response, 'Open Complaints')
        self.assertContains(response, 'Pending Room Requests')
        self.assertContains(response, 'Pending Leave Requests')

    def test_known_fixture_counts_match_source_modules(self):
        """FR-14 / AC-14.1 / ADR-005: Four distinct counts match source module statuses."""
        # 1. Finance: 2 Pending, 1 Verified, 1 Rejected -> expect 2
        finance_services.add_payment(1, '500.00', status=Payment.STATUS_PENDING)
        finance_services.add_payment(2, '300.00', status=Payment.STATUS_PENDING)
        finance_services.add_payment(1, '200.00', status=Payment.STATUS_VERIFIED)
        finance_services.add_payment(3, '100.00', status=Payment.STATUS_REJECTED)

        # 2. Complaints: 1 Submitted, 1 In Progress, 1 Resolved -> expect 2
        ComplaintService.submit_complaint(self.student1, 'Electrical', 'Fan not working')
        c2 = ComplaintService.submit_complaint(self.student2, 'Plumbing', 'Tap leaking')
        ComplaintService.update_complaint_status(c2.pk, 'In Progress', 'Assigned plumber')
        c3 = ComplaintService.submit_complaint(self.student3, 'Cleanliness', 'Floor dirty')
        ComplaintService.update_complaint_status(c3.pk, 'In Progress', 'Assigned')
        ComplaintService.update_complaint_status(c3.pk, 'Resolved', 'Cleaned')

        # 3. Rooms: 1 Change Pending, 1 Swap Pending Warden Approval, 1 Swap Pending Consent -> expect 2
        Student.objects.create(
            student_id='STU-D01', full_name='Student One',
            contact_number='03001111111', guardian_name='G1',
            guardian_contact_number='03001111112', status=Student.STATUS_ACTIVE,
            user_id=self.student1.pk,
        )
        Student.objects.create(
            student_id='STU-D02', full_name='Student Two',
            contact_number='03002222221', guardian_name='G2',
            guardian_contact_number='03002222222', status=Student.STATUS_ACTIVE,
            user_id=self.student2.pk,
        )
        Student.objects.create(
            student_id='STU-D03', full_name='Student Three',
            contact_number='03003333331', guardian_name='G3',
            guardian_contact_number='03003333332', status=Student.STATUS_ACTIVE,
            user_id=self.student3.pk,
        )
        room_a = room_service.create_room('D-101', 2)
        room_b = room_service.create_room('D-102', 3)
        room_service.assign_student(str(self.student1.pk), room_a.id)
        room_service.assign_student(str(self.student2.pk), room_b.id)
        room_service.assign_student(str(self.student3.pk), room_b.id)

        hostel_services.submit_change_request('STU-D01', room_b.id, 'Move to D-102')
        swap_warden = hostel_services.submit_swap_request('STU-D02', 'STU-D01', 'Swap rooms')
        hostel_services.respond_to_swap(swap_warden.pk, 'STU-D01', accept=True)
        # Swap still awaiting student consent must NOT be counted as warden-pending
        hostel_services.submit_swap_request('STU-D03', 'STU-D01', 'Swap pending consent')
        self.assertEqual(RoomRequest.objects.count(), 3)

        # 4. Leave requests (via service interface mock until VS-15 is merged)
        with patch('dashboard.services._resolve_leave_pending_count', return_value=(4, True)):
            self.client.force_login(self.warden)
            response = self.client.get(reverse('dashboard:warden_dashboard'))

        self.assertEqual(response.status_code, 200)
        summary = response.context['pending_summary']
        self.assertEqual(summary['pending_payment_proofs'], 2)
        self.assertEqual(summary['pending_complaints'], 2)
        self.assertEqual(summary['pending_room_requests'], 2)
        self.assertEqual(summary['pending_leave_requests'], 4)
        self.assertEqual(summary['total_pending'], 10)

        # Also verify accounts:dashboard renders the same summary for warden
        with patch('dashboard.services._resolve_leave_pending_count', return_value=(4, True)):
            acc_resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(acc_resp.status_code, 200)
        self.assertEqual(acc_resp.context['pending_summary']['total_pending'], 10)

    def test_dashboard_reads_through_service_interfaces_only(self):
        """ADR-005: Dashboard calls module service functions rather than querying models directly."""
        with (
            patch('dashboard.services.finance_services.count_pending_payments', return_value=3) as m_fin,
            patch('dashboard.services.ComplaintService.get_pending_count', return_value=5) as m_cmp,
            patch('dashboard.services.hostel_services.get_pending_request_count', return_value=2) as m_rom,
        ):
            summary = get_warden_pending_summary(leave_count_provider=lambda: 1)

        m_fin.assert_called_once_with()
        m_cmp.assert_called_once_with()
        m_rom.assert_called_once_with()
        self.assertEqual(summary['pending_payment_proofs'], 3)
        self.assertEqual(summary['pending_complaints'], 5)
        self.assertEqual(summary['pending_room_requests'], 2)
        self.assertEqual(summary['pending_leave_requests'], 1)
        self.assertEqual(summary['total_pending'], 11)
        self.assertTrue(summary['leave_module_available'])

    def test_ac_14_2_student_denied_on_warden_dashboard_and_anonymous_redirected(self):
        """AC-14.2 / NFR-01: Student direct URL access to warden dashboard is denied (403)."""
        anon_resp = self.client.get(reverse('dashboard:warden_dashboard'))
        self.assertEqual(anon_resp.status_code, 302)

        self.client.force_login(self.student1)
        stu_resp = self.client.get(reverse('dashboard:warden_dashboard'))
        self.assertEqual(stu_resp.status_code, 403)

        # Student visiting accounts:dashboard sees student portal, not warden pending summary
        stu_home = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(stu_home.status_code, 200)
        self.assertTemplateUsed(stu_home, 'accounts/student_dashboard.html')
        self.assertNotIn('pending_summary', stu_home.context)

    def test_nfr_04_warden_dashboard_loads_within_3_seconds(self):
        """NFR-04 (provisional): Warden dashboard responds well within 3.0 seconds."""
        self.client.force_login(self.warden)
        start = time.perf_counter()
        response = self.client.get(reverse('dashboard:warden_dashboard'))
        elapsed = time.perf_counter() - start
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0)
