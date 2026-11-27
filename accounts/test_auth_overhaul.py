from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class AuthOverhaulTests(TestCase):
    def setUp(self):
        self.main_warden = User.objects.create_user(
            username='adnan',
            password='adnan@1302',
            role='warden',
            full_name='Adnan',
            email='adnan0734736@gmail.com',
            mobile_number='03440734736',
            is_main_warden=True,
            is_staff=True,
        )
        self.sub_warden = User.objects.create_user(
            username='warden_sub',
            password='SubPassword123',
            role='warden',
            full_name='Sub Warden',
            email='sub@hostelease.local',
            mobile_number='03009998877',
            is_main_warden=False,
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username='STU-900',
            password='StudentPassword123',
            role='student',
            student_id='STU-900',
            email='stu900@hostelease.local',
            mobile_number='03001112233',
        )

    def test_seed_main_warden_purges_and_seeds_adnan(self):
        call_command('seed_main_warden')
        self.assertEqual(User.objects.count(), 1)
        seeded = User.objects.get(username='adnan')
        self.assertTrue(seeded.check_password('adnan@1302'))
        self.assertTrue(seeded.is_main_warden)
        self.assertEqual(seeded.email, 'adnan0734736@gmail.com')
        self.assertEqual(seeded.mobile_number, '03440734736')
        self.assertEqual(seeded.role, 'warden')
        self.assertFalse(seeded.must_change_password)

    def test_add_warden_keeps_current_warden_logged_in_and_forces_temp_change(self):
        self.client.force_login(self.main_warden)
        resp = self.client.post(
            reverse('accounts:warden_create'),
            {
                'full_name': 'Warden Two',
                'username': 'warden_two',
                'email': 'warden2@hostelease.local',
                'mobile_number': '03005556677',
                'temporary_password': '',
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'accounts/warden_create_success.html')
        self.assertContains(resp, 'warden_two')
        self.assertContains(resp, 'Copy Credentials')

        # Critical: current warden session must remain unchanged
        self.assertEqual(int(self.client.session['_auth_user_id']), self.main_warden.pk)

        created = User.objects.get(username='warden_two')
        self.assertFalse(created.is_main_warden)
        self.assertEqual(created.role, 'warden')
        self.assertTrue(created.must_change_password)

        # New warden logs in with temp password -> forced to change password
        temp_pw = resp.context['temporary_password']
        self.client.logout()
        login_resp = self.client.post(
            reverse('accounts:login'),
            {'username': 'warden_two', 'password': temp_pw},
        )
        self.assertRedirects(login_resp, reverse('accounts:change_password'))

    def test_main_warden_forgot_password_only_allows_main_warden(self):
        # Sub-warden denied self-service forgot password
        sub_resp = self.client.post(
            reverse('accounts:forgot_password'),
            {
                'username': 'warden_sub',
                'email': 'sub@hostelease.local',
                'mobile_number': '03009998877',
                'new_password': 'NewPassword123',
                'confirm_password': 'NewPassword123',
            },
        )
        self.assertEqual(sub_resp.status_code, 403)
        self.assertContains(sub_resp, 'contact the Main Warden', status_code=403)

        # Student denied self-service forgot password
        stu_resp = self.client.post(
            reverse('accounts:forgot_password'),
            {
                'username': 'STU-900',
                'email': 'stu900@hostelease.local',
                'mobile_number': '03001112233',
                'new_password': 'NewPassword123',
                'confirm_password': 'NewPassword123',
            },
        )
        self.assertEqual(stu_resp.status_code, 403)

        # Main Warden succeeds when email & mobile match
        ok_resp = self.client.post(
            reverse('accounts:forgot_password'),
            {
                'username': 'adnan',
                'email': 'adnan0734736@gmail.com',
                'mobile_number': '03440734736',
                'new_password': 'NewMainPassword123',
                'confirm_password': 'NewMainPassword123',
            },
        )
        self.assertRedirects(ok_resp, reverse('accounts:login'))
        self.main_warden.refresh_from_db()
        self.assertTrue(self.main_warden.check_password('NewMainPassword123'))

    def test_sub_warden_reset_by_main_warden_and_expiry(self):
        # Non-main warden cannot reset another warden's password
        self.client.force_login(self.sub_warden)
        denied = self.client.get(reverse('accounts:warden_reset_password', args=[self.sub_warden.pk]))
        self.assertEqual(denied.status_code, 403)

        # Main warden resets sub-warden password
        self.client.force_login(self.main_warden)
        reset_resp = self.client.post(
            reverse('accounts:warden_reset_password', args=[self.sub_warden.pk]),
            {
                'main_warden_password': 'adnan@1302',
                'temporary_password': 'TempResetPassword1',
            },
        )
        self.assertEqual(reset_resp.status_code, 200)
        self.assertTemplateUsed(reset_resp, 'accounts/warden_reset_success.html')
        self.assertEqual(int(self.client.session['_auth_user_id']), self.main_warden.pk)

        self.sub_warden.refresh_from_db()
        self.assertTrue(self.sub_warden.must_change_password)
        self.assertIsNotNone(self.sub_warden.password_reset_expires_at)

        # Expired reset password is rejected on login
        self.sub_warden.password_reset_expires_at = timezone.now() - timedelta(minutes=5)
        self.sub_warden.save()
        self.client.logout()
        expired_login = self.client.post(
            reverse('accounts:login'),
            {'username': 'warden_sub', 'password': 'TempResetPassword1'},
        )
        self.assertEqual(expired_login.status_code, 200)
        self.assertContains(expired_login, 'expired')

        # Valid (unexpired) reset password logs in and forces password change
        self.sub_warden.password_reset_expires_at = timezone.now() + timedelta(hours=2)
        self.sub_warden.save()
        ok_login = self.client.post(
            reverse('accounts:login'),
            {'username': 'warden_sub', 'password': 'TempResetPassword1'},
        )
        self.assertRedirects(ok_login, reverse('accounts:change_password'))

    def test_warden_profile_update_and_uniqueness(self):
        self.client.force_login(self.sub_warden)
        resp = self.client.post(
            reverse('accounts:warden_profile'),
            {
                'full_name': 'Updated Sub Warden',
                'email': 'updated_sub@hostelease.local',
                'mobile_number': '03007778899',
            },
        )
        self.assertRedirects(resp, reverse('accounts:warden_profile'))
        self.sub_warden.refresh_from_db()
        self.assertEqual(self.sub_warden.full_name, 'Updated Sub Warden')
        self.assertEqual(self.sub_warden.email, 'updated_sub@hostelease.local')
        self.assertEqual(self.sub_warden.mobile_number, '03007778899')

        # Duplicate email belonging to Main Warden is rejected
        dup_resp = self.client.post(
            reverse('accounts:warden_profile'),
            {
                'full_name': 'Updated Sub Warden',
                'email': 'adnan0734736@gmail.com',
                'mobile_number': '03007778899',
            },
        )
        self.assertEqual(dup_resp.status_code, 200)
        self.assertContains(dup_resp, 'already used')
