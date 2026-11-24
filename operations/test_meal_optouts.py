from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import meal_service
from .meal_service import MealOptOutError
from .models import MealOptOut

User = get_user_model()


class MealOptOutTests(TestCase):
    """Tests for VS-18: Student meal opt-out & warden summary (FR-19, AC-19.1-19.5, EC-50, EC-51)."""

    def setUp(self):
        self.warden = User.objects.create_user(
            username='warden_vs18', password='WardenPassword123!', role='warden', is_staff=True
        )
        self.stu1 = User.objects.create_user(
            username='STU-1801', password='StudentPassword123!', role='student', student_id='STU-1801'
        )
        self.stu2 = User.objects.create_user(
            username='STU-1802', password='StudentPassword123!', role='student', student_id='STU-1802'
        )
        self.today = timezone.localdate()
        self.future = self.today + timedelta(days=2)
        self.past = self.today - timedelta(days=1)

    def test_ac_19_1_valid_future_opt_out_saved_as_active(self):
        self.client.force_login(self.stu1)
        resp = self.client.post(
            reverse('operations:student_meal_optouts'),
            {'meal_date': self.future.isoformat(), 'meal_type': MealOptOut.MEAL_LUNCH},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Active')
        opt = MealOptOut.objects.get(student_id='STU-1801')
        self.assertEqual(opt.status, MealOptOut.STATUS_ACTIVE)
        self.assertEqual(opt.meal_type, MealOptOut.MEAL_LUNCH)

    def test_ac_19_2_ec_50_past_date_rejected(self):
        self.client.force_login(self.stu1)
        resp = self.client.post(
            reverse('operations:student_meal_optouts'),
            {'meal_date': self.past.isoformat(), 'meal_type': MealOptOut.MEAL_DINNER},
            follow=True,
        )
        self.assertContains(resp, 'past date')
        self.assertEqual(MealOptOut.objects.count(), 0)

    def test_invalid_meal_type_and_duplicate_active_rejected(self):
        with self.assertRaises(MealOptOutError):
            meal_service.create_opt_out(student_id='STU-1801', meal_date=self.future, meal_type='Brunch')
        meal_service.create_opt_out(student_id='STU-1801', meal_date=self.future, meal_type=MealOptOut.MEAL_BREAKFAST)
        with self.assertRaises(MealOptOutError):
            meal_service.create_opt_out(student_id='STU-1801', meal_date=self.future, meal_type=MealOptOut.MEAL_BREAKFAST)

    def test_ac_19_3_cancel_before_meal_date_retains_cancelled_record(self):
        opt = meal_service.create_opt_out(
            student_id='STU-1801', meal_date=self.future, meal_type=MealOptOut.MEAL_DINNER
        )
        self.client.force_login(self.stu1)
        resp = self.client.post(
            reverse('operations:student_cancel_meal_optout', args=[opt.pk]),
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        opt.refresh_from_db()
        self.assertEqual(opt.status, MealOptOut.STATUS_CANCELLED)
        self.assertIsNotNone(opt.cancelled_at)
        self.assertEqual(MealOptOut.objects.count(), 1)

    def test_ac_19_4_ec_51_cancel_after_meal_date_passed_rejected(self):
        opt = MealOptOut.objects.create(
            student_id='STU-1801',
            meal_date=self.past,
            meal_type=MealOptOut.MEAL_LUNCH,
            status=MealOptOut.STATUS_ACTIVE,
        )
        self.client.force_login(self.stu1)
        resp = self.client.post(
            reverse('operations:student_cancel_meal_optout', args=[opt.pk]),
            follow=True,
        )
        self.assertContains(resp, 'after the meal date has passed')
        opt.refresh_from_db()
        self.assertEqual(opt.status, MealOptOut.STATUS_ACTIVE)

    def test_ac_19_5_warden_summary_counts_active_by_date_and_meal(self):
        d1 = self.future
        d2 = self.future + timedelta(days=1)
        meal_service.create_opt_out(student_id='STU-1801', meal_date=d1, meal_type=MealOptOut.MEAL_BREAKFAST)
        meal_service.create_opt_out(student_id='STU-1802', meal_date=d1, meal_type=MealOptOut.MEAL_BREAKFAST)
        cancelled = meal_service.create_opt_out(student_id='STU-1801', meal_date=d1, meal_type=MealOptOut.MEAL_LUNCH)
        meal_service.cancel_opt_out(opt_out_id=cancelled.pk, student_id='STU-1801')
        meal_service.create_opt_out(student_id='STU-1802', meal_date=d2, meal_type=MealOptOut.MEAL_DINNER)

        self.client.force_login(self.warden)
        resp = self.client.get(reverse('operations:warden_meal_optout_summary'))
        self.assertEqual(resp.status_code, 200)
        rows = {r['meal_date']: r for r in resp.context['summary_rows']}
        self.assertEqual(rows[d1]['breakfast'], 2)
        self.assertEqual(rows[d1]['lunch'], 0)
        self.assertEqual(rows[d1]['total'], 2)
        self.assertEqual(rows[d2]['dinner'], 1)
        self.assertEqual(rows[d2]['total'], 1)

    def test_access_control_cross_student_and_br05(self):
        opt = meal_service.create_opt_out(
            student_id='STU-1801', meal_date=self.future, meal_type=MealOptOut.MEAL_LUNCH
        )
        # Cross-student cancel blocked
        self.client.force_login(self.stu2)
        self.client.post(reverse('operations:student_cancel_meal_optout', args=[opt.pk]))
        opt.refresh_from_db()
        self.assertEqual(opt.status, MealOptOut.STATUS_ACTIVE)

        # Student denied on warden summary (403)
        self.assertEqual(self.client.get(reverse('operations:warden_meal_optout_summary')).status_code, 403)
        # Warden denied on student opt-outs (403)
        self.client.force_login(self.warden)
        self.assertEqual(self.client.get(reverse('operations:student_meal_optouts')).status_code, 403)
        # Anonymous redirected (302)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('operations:student_meal_optouts')).status_code, 302)
        self.assertEqual(self.client.get(reverse('operations:warden_meal_optout_summary')).status_code, 302)
        # Hard delete blocked (BR-05)
        with self.assertRaises(PermissionError):
            opt.delete()
