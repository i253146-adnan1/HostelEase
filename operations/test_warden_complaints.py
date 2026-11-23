from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .complaint_service import ComplaintError, ComplaintService
from .models import Complaint

User = get_user_model()


class WardenComplaintServiceTests(TestCase):
    """Service-layer tests for VS-13 warden complaint management (FR-08, BR-04, OQ-03, OQ-12)."""

    def setUp(self):
        self.student = User.objects.create_user(
            username='student1',
            password='Password123!',
            role='student',
        )
        self.complaint = ComplaintService.submit_complaint(
            student_user=self.student,
            category='electricity_water',
            description='Ceiling fan in room 12 is not working.',
        )

    def test_allowed_transition_submitted_to_in_progress_to_resolved(self):
        """AC-08.1: Warden moves Submitted -> In Progress -> Resolved with remark."""
        updated = ComplaintService.update_complaint_status(
            self.complaint.pk,
            'In Progress',
            remark='Electrician assigned.',
        )
        self.assertEqual(updated.status, 'In Progress')
        self.assertEqual(updated.warden_remark, 'Electrician assigned.')

        resolved = ComplaintService.update_complaint_status(
            self.complaint.pk,
            'Resolved',
            remark='Fan capacitor replaced and tested.',
        )
        self.assertEqual(resolved.status, 'Resolved')
        self.assertEqual(resolved.warden_remark, 'Fan capacitor replaced and tested.')

    def test_in_progress_allows_empty_remark(self):
        """Remark is optional when moving Submitted -> In Progress."""
        updated = ComplaintService.update_complaint_status(
            self.complaint.pk,
            'In Progress',
            remark='',
        )
        self.assertEqual(updated.status, 'In Progress')
        self.assertEqual(updated.warden_remark, '')

    def test_resolved_requires_non_empty_remark_oq_12(self):
        """OQ-12 / EC-40: Marking Resolved without a remark raises ComplaintError."""
        ComplaintService.update_complaint_status(self.complaint.pk, 'In Progress')

        for blank_remark in ('', '   ', '\n\t'):
            with self.subTest(blank_remark=repr(blank_remark)):
                with self.assertRaises(ComplaintError):
                    ComplaintService.update_complaint_status(
                        self.complaint.pk,
                        'Resolved',
                        remark=blank_remark,
                    )
                self.complaint.refresh_from_db()
                self.assertEqual(self.complaint.status, 'In Progress')

    def test_invalid_transitions_blocked_br_04_oq_03(self):
        """BR-04 / OQ-03: Skipping states, backward transitions, and reopening Resolved are blocked."""
        # Cannot skip Submitted -> Resolved
        with self.assertRaises(ComplaintError):
            ComplaintService.update_complaint_status(
                self.complaint.pk, 'Resolved', remark='Skipped step'
            )

        # Cannot transition Submitted -> Submitted
        with self.assertRaises(ComplaintError):
            ComplaintService.update_complaint_status(self.complaint.pk, 'Submitted')

        # Move to In Progress, cannot go back to Submitted
        ComplaintService.update_complaint_status(self.complaint.pk, 'In Progress')
        with self.assertRaises(ComplaintError):
            ComplaintService.update_complaint_status(self.complaint.pk, 'Submitted')

        # Move to Resolved, cannot reopen to In Progress, Submitted, or Resolved (OQ-03)
        ComplaintService.update_complaint_status(
            self.complaint.pk, 'Resolved', remark='Fixed.'
        )
        for target in ('Submitted', 'In Progress', 'Resolved'):
            with self.subTest(reopen_target=target):
                with self.assertRaises(ComplaintError):
                    ComplaintService.update_complaint_status(
                        self.complaint.pk, target, remark='Trying to reopen'
                    )

    def test_nonexistent_complaint_raises_complaint_error(self):
        """Updating a nonexistent complaint ID raises ComplaintError."""
        with self.assertRaises(ComplaintError):
            ComplaintService.update_complaint_status(999999, 'In Progress')

    def test_pending_count_reflects_resolution_adr_005(self):
        """ADR-005: get_pending_count() counts Submitted and In Progress, not Resolved."""
        self.assertEqual(ComplaintService.get_pending_count(), 1)
        ComplaintService.update_complaint_status(self.complaint.pk, 'In Progress')
        self.assertEqual(ComplaintService.get_pending_count(), 1)
        ComplaintService.update_complaint_status(
            self.complaint.pk, 'Resolved', remark='Done.'
        )
        self.assertEqual(ComplaintService.get_pending_count(), 0)

    def test_complaint_cannot_be_hard_deleted_br_05(self):
        """BR-05: Complaint records are never hard-deleted."""
        with self.assertRaises(PermissionError):
            self.complaint.delete()


class WardenComplaintViewTests(TestCase):
    """HTTP view & role-isolation tests for VS-13 (FR-08, AC-08.1, NFR-01)."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden1',
            password='Password123!',
            role='warden',
        )
        self.student = User.objects.create_user(
            username='student_a',
            password='Password123!',
            role='student',
        )
        self.complaint = ComplaintService.submit_complaint(
            student_user=self.student,
            category='internet',
            description='Wi-Fi drops repeatedly on 2nd floor.',
        )
        self.warden_client = Client()
        self.warden_client.force_login(self.warden)
        self.student_client = Client()
        self.student_client.force_login(self.student)

    def test_warden_list_and_status_filter(self):
        """Warden can view all complaints and filter by status."""
        c2 = ComplaintService.submit_complaint(
            student_user=self.student,
            category='food_mess',
            description='Dinner served cold.',
        )
        ComplaintService.update_complaint_status(c2.pk, 'In Progress')

        resp_all = self.warden_client.get(reverse('operations:warden_complaint_list'))
        self.assertEqual(resp_all.status_code, 200)
        self.assertContains(resp_all, 'Internet')
        self.assertContains(resp_all, 'Food and Mess')

        resp_sub = self.warden_client.get(
            reverse('operations:warden_complaint_list') + '?status=Submitted'
        )
        self.assertEqual(resp_sub.status_code, 200)
        self.assertContains(resp_sub, 'Internet')
        self.assertNotContains(resp_sub, 'Food and Mess')

    def test_warden_transitions_and_student_sees_status_and_remark(self):
        """AC-08.1: Warden transitions complaint via POST and student sees updated status & remark."""
        update_url = reverse('operations:warden_complaint_update', args=[self.complaint.pk])

        # Move to In Progress
        resp1 = self.warden_client.post(
            update_url,
            {'status': 'In Progress', 'warden_remark': 'Router check scheduled.'},
        )
        self.assertRedirects(
            resp1,
            reverse('operations:warden_complaint_detail', args=[self.complaint.pk]),
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'In Progress')

        # Attempt Resolved without remark -> stays In Progress
        resp_fail = self.warden_client.post(
            update_url,
            {'status': 'Resolved', 'warden_remark': '   '},
        )
        self.assertRedirects(
            resp_fail,
            reverse('operations:warden_complaint_detail', args=[self.complaint.pk]),
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'In Progress')

        # Move to Resolved with remark
        resp2 = self.warden_client.post(
            update_url,
            {'status': 'Resolved', 'warden_remark': 'Access point replaced.'},
        )
        self.assertRedirects(
            resp2,
            reverse('operations:warden_complaint_detail', args=[self.complaint.pk]),
        )
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'Resolved')
        self.assertEqual(self.complaint.warden_remark, 'Access point replaced.')

        # Student sees updated status and remark on their own detail page
        student_resp = self.student_client.get(
            reverse('operations:complaint_detail', args=[self.complaint.pk])
        )
        self.assertEqual(student_resp.status_code, 200)
        self.assertContains(student_resp, 'Resolved')
        self.assertContains(student_resp, 'Access point replaced.')

    def test_warden_detail_shows_no_reopen_controls_when_resolved(self):
        """OQ-03: Resolved complaint detail page has no reopen form."""
        ComplaintService.update_complaint_status(self.complaint.pk, 'In Progress')
        ComplaintService.update_complaint_status(
            self.complaint.pk, 'Resolved', remark='Resolved cleanly.'
        )
        resp = self.warden_client.get(
            reverse('operations:warden_complaint_detail', args=[self.complaint.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Reopening is not enabled')
        self.assertNotContains(resp, 'Mark as In Progress')
        self.assertNotContains(resp, 'Mark as Submitted')

    def test_student_cannot_access_warden_complaint_views_or_update(self):
        """NFR-01 / AC-08.1: Student receives 403 Forbidden on warden complaint routes."""
        urls = [
            reverse('operations:warden_complaint_list'),
            reverse('operations:warden_complaint_detail', args=[self.complaint.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                resp = self.student_client.get(url)
                self.assertEqual(resp.status_code, 403)

        post_resp = self.student_client.post(
            reverse('operations:warden_complaint_update', args=[self.complaint.pk]),
            {'status': 'In Progress', 'warden_remark': 'Unauthorized'},
        )
        self.assertEqual(post_resp.status_code, 403)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'Submitted')

    def test_anonymous_user_redirected_to_login(self):
        """NFR-01: Anonymous user is redirected to login on all warden complaint URLs."""
        anon = Client()
        for url in (
            reverse('operations:warden_complaint_list'),
            reverse('operations:warden_complaint_detail', args=[self.complaint.pk]),
            reverse('operations:warden_complaint_update', args=[self.complaint.pk]),
        ):
            with self.subTest(url=url):
                resp = anon.get(url)
                self.assertEqual(resp.status_code, 302)
                self.assertIn('/accounts/login/', resp.url)
