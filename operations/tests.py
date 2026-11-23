from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from . import feedback_service
from .complaint_service import ComplaintService
from .feedback_service import FeedbackError, FeedbackValidationError
from .models import Complaint, Feedback, StoredFile

User = get_user_model()


class FeedbackServiceTests(TestCase):
    """Unit tests for feedback_service and core business rules (VS-07)."""

    def setUp(self):
        self.student_id = 'STU-101'

    def test_ac_15_1_valid_feedback_submission(self):
        """AC-15.1: Student submits valid 1-5 ratings for all 4 aspects."""
        fb = feedback_service.submit_feedback(
            student_id=self.student_id,
            food=4,
            room=5,
            washroom=3,
            environment=4,
        )

        self.assertIsNotNone(fb.pk)
        self.assertEqual(fb.student_id, self.student_id)
        self.assertEqual(fb.food_rating, 4)
        self.assertEqual(fb.room_rating, 5)
        self.assertEqual(fb.washroom_rating, 3)
        self.assertEqual(fb.environment_rating, 4)
        self.assertEqual(Feedback.objects.count(), 1)

    def test_ac_15_2_ratings_outside_range_rejected(self):
        """AC-15.2: Ratings < 1 or > 5 or non-integers are rejected; nothing saved."""
        invalid_ratings = [0, 6, -1, 10, 'abc', '3.5', None, '']

        for invalid in invalid_ratings:
            with self.subTest(invalid_rating=invalid):
                with self.assertRaises(FeedbackValidationError):
                    feedback_service.submit_feedback(
                        student_id=self.student_id,
                        food=invalid,
                        room=4,
                        washroom=4,
                        environment=4,
                    )
                self.assertEqual(Feedback.objects.count(), 0)

    def test_ac_15_2_missing_aspect_rejected(self):
        """AC-15.2: All four aspects are mandatory; missing any raises error."""
        aspect_keys = ['food', 'room', 'washroom', 'environment']
        base = {'food': 5, 'room': 5, 'washroom': 5, 'environment': 5}

        for missing in aspect_keys:
            kw = base.copy()
            kw[missing] = None
            with self.subTest(missing_aspect=missing):
                with self.assertRaises(FeedbackValidationError):
                    feedback_service.submit_feedback(
                        student_id=self.student_id,
                        **kw
                    )
                self.assertEqual(Feedback.objects.count(), 0)

    def test_ac_15_3_repeated_submissions_create_separate_entries(self):
        """AC-15.3: Multiple submissions by same student create distinct retained entries."""
        fb1 = feedback_service.submit_feedback(
            student_id=self.student_id,
            food=3, room=3, washroom=3, environment=3,
        )
        fb2 = feedback_service.submit_feedback(
            student_id=self.student_id,
            food=5, room=4, washroom=4, environment=5,
        )

        self.assertNotEqual(fb1.pk, fb2.pk)
        self.assertEqual(Feedback.objects.count(), 2)

        # Earlier feedback remains unchanged
        fb1_reloaded = Feedback.objects.get(pk=fb1.pk)
        self.assertEqual(fb1_reloaded.food_rating, 3)

        # Student history returns both entries
        history = list(feedback_service.list_student_feedback(self.student_id))
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].pk, fb2.pk)  # Newest first

    def test_br_11_immutability_of_feedback_records(self):
        """BR-11: Submitted feedback cannot be edited once saved."""
        fb = feedback_service.submit_feedback(
            student_id=self.student_id,
            food=4, room=4, washroom=4, environment=4,
        )

        fb.food_rating = 1
        with self.assertRaises(PermissionError):
            fb.save()

    def test_br_05_feedback_records_never_deleted(self):
        """BR-05: Feedback records cannot be hard deleted."""
        fb = feedback_service.submit_feedback(
            student_id=self.student_id,
            food=4, room=4, washroom=4, environment=4,
        )

        with self.assertRaises(PermissionError):
            fb.delete()

    def test_ac_15_4_feedback_summary_aggregation(self):
        """AC-15.4: Warden summary aggregates counts per star level per aspect."""
        # Setup known fixture: 3 submissions
        # Submission 1: food=5, room=4, washroom=3, env=2
        feedback_service.submit_feedback('STU-1', 5, 4, 3, 2)
        # Submission 2: food=5, room=5, washroom=3, env=4
        feedback_service.submit_feedback('STU-2', 5, 5, 3, 4)
        # Submission 3: food=1, room=2, washroom=3, env=5
        feedback_service.submit_feedback('STU-3', 1, 2, 3, 5)

        summary = feedback_service.get_feedback_summary()

        self.assertEqual(summary['total_submissions'], 3)

        # Food: two 5-stars, one 1-star -> avg = (5+5+1)/3 = 3.67
        food = summary['aspects']['food']
        self.assertEqual(food['counts'][5], 2)
        self.assertEqual(food['counts'][1], 1)
        self.assertEqual(food['counts'][4], 0)
        self.assertAlmostEqual(food['average'], 3.67, places=2)
        self.assertEqual(food['percentages'][5], 66.7)
        self.assertEqual(food['percentages'][1], 33.3)

        # Washrooms: three 3-stars -> avg = 3.0
        washroom = summary['aspects']['washroom']
        self.assertEqual(washroom['counts'][3], 3)
        self.assertEqual(washroom['counts'][1], 0)
        self.assertEqual(washroom['average'], 3.0)
        self.assertEqual(washroom['percentages'][3], 100.0)

    def test_feedback_summary_empty_state(self):
        """Warden summary handles 0 submissions cleanly without errors."""
        summary = feedback_service.get_feedback_summary()
        self.assertEqual(summary['total_submissions'], 0)
        for key, aspect in summary['aspects'].items():
            self.assertEqual(aspect['average'], 0.0)
            for s in range(1, 6):
                self.assertEqual(aspect['counts'][s], 0)
                self.assertEqual(aspect['percentages'][s], 0.0)


class FeedbackViewTests(TestCase):
    """Integration & access control tests for feedback views (VS-07, NFR-01)."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden1',
            password='WardenPassword123',
            role='warden',
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student1',
            password='StudentPassword123',
            role='student',
            student_id='STU-201',
        )

    def test_nfr_01_anonymous_redirected_to_login(self):
        """Anonymous access to feedback routes is redirected to login."""
        urls = [
            reverse('operations:student_feedback'),
            reverse('operations:warden_feedback_summary'),
        ]
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/accounts/login/', resp.url)

    def test_nfr_01_student_denied_warden_summary(self):
        """Student role receives 403 Forbidden on warden feedback summary."""
        self.client.force_login(self.student)
        resp = self.client.get(reverse('operations:warden_feedback_summary'))
        self.assertEqual(resp.status_code, 403)

    def test_nfr_01_warden_denied_student_feedback_form(self):
        """Warden role receives 403 Forbidden on student feedback submission form."""
        self.client.force_login(self.warden)
        resp = self.client.get(reverse('operations:student_feedback'))
        self.assertEqual(resp.status_code, 403)

        post_resp = self.client.post(reverse('operations:student_feedback'), {})
        self.assertEqual(post_resp.status_code, 403)

    def test_student_can_view_and_submit_feedback(self):
        """Student opens feedback form, submits ratings, and sees success message."""
        self.client.force_login(self.student)

        # GET form
        get_resp = self.client.get(reverse('operations:student_feedback'))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'Hostel Feedback')
        self.assertContains(get_resp, 'Food &amp; Mess')

        # POST submission
        payload = {
            'food_rating': '4',
            'room_rating': '5',
            'washroom_rating': '4',
            'environment_rating': '5',
        }
        post_resp = self.client.post(
            reverse('operations:student_feedback'),
            payload,
            follow=True,
        )
        self.assertEqual(post_resp.status_code, 200)
        self.assertContains(post_resp, 'Thank you! Your feedback has been recorded successfully.')
        self.assertEqual(Feedback.objects.count(), 1)

        # History is visible on the page
        self.assertContains(post_resp, 'Your Submission History')

    def test_warden_can_view_feedback_summary(self):
        """Warden can open the summary and view aggregated data."""
        feedback_service.submit_feedback('STU-A', 5, 4, 3, 5)
        feedback_service.submit_feedback('STU-B', 4, 4, 4, 4)

        self.client.force_login(self.warden)
        resp = self.client.get(reverse('operations:warden_feedback_summary'))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Hostel Feedback Summary')
        self.assertContains(resp, 'Total Submissions Recorded')
        self.assertContains(resp, 'Food &amp; Mess')
        self.assertContains(resp, 'Rooms &amp; Maintenance')
        self.assertContains(resp, 'Washrooms &amp; Cleanliness')
        self.assertContains(resp, 'Hostel Environment')


class ComplaintSubmissionTests(TestCase):
    def setUp(self):
        self.student1 = User.objects.create_user(
            username='student1', password='testpass123', role='student'
        )
        self.student2 = User.objects.create_user(
            username='student2', password='testpass123', role='student'
        )
        self.warden = User.objects.create_user(
            username='warden1', password='testpass123', role='warden', is_staff=True
        )
        self.client = Client()

    # AC-07.1 — Test 1
    def test_valid_complaint_no_attachment_saved_as_submitted(self):
        complaint = ComplaintService.submit_complaint(
            self.student1, 'internet', 'WiFi not working'
        )
        self.assertEqual(complaint.status, 'Submitted')
        self.assertEqual(complaint.category, 'internet')
        self.assertIsNone(complaint.attachment)

    # AC-07.1 — Test 2: POST via view, valid form
    def test_valid_complaint_post_redirects_to_list(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('operations:complaint_submit'), {
            'category': 'internet',
            'description': 'WiFi very slow',
        })
        self.assertRedirects(response, reverse('operations:complaint_list'))
        self.assertEqual(Complaint.objects.filter(student_user=self.student1).count(), 1)

    # AC-07.2 — Test 3: Missing category
    def test_missing_category_complaint_not_saved(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('operations:complaint_submit'), {
            'description': 'Some problem',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)

    # AC-07.2 — Test 4: Missing description
    def test_missing_description_complaint_not_saved(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('operations:complaint_submit'), {
            'category': 'internet',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)

    # AC-07.3 — Test 5: .txt attachment rejected
    def test_invalid_attachment_type_rejected(self):
        self.client.login(username='student1', password='testpass123')
        bad_file = SimpleUploadedFile('report.txt', b'hello', content_type='text/plain')
        response = self.client.post(reverse('operations:complaint_submit'), {
            'category': 'internet',
            'description': 'Problem',
            'attachment': bad_file,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)

    # AC-07.3 — Test 6: Oversized attachment rejected
    def test_oversized_attachment_rejected(self):
        self.client.login(username='student1', password='testpass123')
        big_data = b'\xff\xd8\xff' + b'x' * (5 * 1024 * 1024 + 1)
        big_file = SimpleUploadedFile('big.jpg', big_data, content_type='image/jpeg')
        response = self.client.post(reverse('operations:complaint_submit'), {
            'category': 'internet',
            'description': 'Problem',
            'attachment': big_file,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Complaint.objects.count(), 0)

    # AC-07.4 — Test 7: Student views own complaint detail
    def test_student_views_own_complaint_detail(self):
        complaint = ComplaintService.submit_complaint(
            self.student1, 'internet', 'WiFi not working'
        )
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(
            reverse('operations:complaint_detail', args=[complaint.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'WiFi not working')

    # NFR-01 — Test 8: Student cannot view another student's complaint
    def test_student_cannot_view_other_student_complaint(self):
        complaint = ComplaintService.submit_complaint(
            self.student1, 'internet', 'Private complaint'
        )
        self.client.login(username='student2', password='testpass123')
        response = self.client.get(
            reverse('operations:complaint_detail', args=[complaint.pk])
        )
        self.assertIn(response.status_code, [403, 404])

    # BR-05 — Test 9: No delete URL exists
    def test_no_delete_url_exists(self):
        from django.urls import NoReverseMatch
        with self.assertRaises(NoReverseMatch):
            reverse('operations:complaint_delete', args=[1])

    # BR-05 — Test 10: Complaint.delete() raises PermissionError
    def test_complaint_model_delete_raises(self):
        complaint = ComplaintService.submit_complaint(
            self.student1, 'internet', 'Test'
        )
        with self.assertRaises(PermissionError):
            complaint.delete()


class ComplaintServiceTests(TestCase):
    def setUp(self):
        self.student1 = User.objects.create_user(
            username='s1', password='pass', role='student'
        )
        self.student2 = User.objects.create_user(
            username='s2', password='pass', role='student'
        )

    # Test 11: get_pending_count returns correct count
    def test_get_pending_count_submitted_and_in_progress(self):
        ComplaintService.submit_complaint(self.student1, 'internet', 'A')
        ComplaintService.submit_complaint(self.student1, 'internet', 'B')
        c = ComplaintService.submit_complaint(self.student1, 'internet', 'C')
        c.status = 'In Progress'
        c.save()
        d = ComplaintService.submit_complaint(self.student1, 'internet', 'D')
        d.status = 'Resolved'
        d.save()
        self.assertEqual(ComplaintService.get_pending_count(), 3)

    # Test 12: get_pending_count excludes Resolved
    def test_get_pending_count_excludes_resolved(self):
        c = ComplaintService.submit_complaint(self.student1, 'internet', 'X')
        c.status = 'Resolved'
        c.save()
        self.assertEqual(ComplaintService.get_pending_count(), 0)

    # Test 13: get_student_complaints returns only own
    def test_get_student_complaints_own_only(self):
        ComplaintService.submit_complaint(self.student1, 'internet', 'A')
        ComplaintService.submit_complaint(self.student2, 'internet', 'B')
        qs = ComplaintService.get_student_complaints(self.student1)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().student_user, self.student1)

    # Test 14: get_complaint_detail raises PermissionDenied for wrong student
    def test_get_complaint_detail_wrong_student_raises(self):
        complaint = ComplaintService.submit_complaint(
            self.student1, 'internet', 'Private'
        )
        with self.assertRaises(PermissionDenied):
            ComplaintService.get_complaint_detail(complaint.pk, self.student2)


class ComplaintAccessTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='stu', password='pass', role='student'
        )
        self.warden = User.objects.create_user(
            username='war', password='pass', role='warden', is_staff=True
        )
        self.client = Client()

    # Test 15: Unauthenticated redirected to login
    def test_unauthenticated_redirected_to_login(self):
        response = self.client.get(reverse('operations:complaint_list'))
        self.assertRedirects(
            response,
            f'/accounts/login/?next={reverse("operations:complaint_list")}',
            fetch_redirect_response=False
        )

    # Test 16: Warden cannot access student complaint submit URL
    def test_warden_cannot_submit_student_complaint(self):
        self.client.login(username='war', password='pass')
        response = self.client.get(reverse('operations:complaint_submit'))
        self.assertEqual(response.status_code, 403)

