from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .guards import login_required_guard, student_required, warden_required
from .models import StudentProfile

User = get_user_model()


class AuthenticationAndGuardsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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
            student_id='STU-001',
        )
        self.inactive_student = User.objects.create_user(
            username='inactive_student',
            password='InactivePassword123',
            role='student',
            is_active=False,
        )

    def test_public_routes_accessible_without_login(self):
        home_resp = self.client.get(reverse('home'))
        login_resp = self.client.get(reverse('accounts:login'))
        self.assertEqual(home_resp.status_code, 200)
        self.assertEqual(login_resp.status_code, 200)
        self.assertNotContains(login_resp, 'Register')

    def test_ac_02_1_valid_warden_login_opens_warden_dashboard(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'warden1', 'password': 'WardenPassword123'},
            follow=True,
        )
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertTemplateUsed(response, 'accounts/warden_dashboard.html')
        self.assertContains(response, 'Warden Portal')

    def test_ac_02_1_valid_student_login_opens_student_dashboard(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'student1', 'password': 'StudentPassword123'},
            follow=True,
        )
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.assertTemplateUsed(response, 'accounts/student_dashboard.html')
        self.assertContains(response, 'Student Portal')

    def test_ac_02_2_wrong_credentials_denied_stays_on_login_page(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'student1', 'password': 'WrongPassword'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertContains(response, 'Invalid username or password.')

    def test_br_09_inactive_user_cannot_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'inactive_student', 'password': 'InactivePassword123'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertContains(response, 'Invalid username or password.')
        dash_resp = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(dash_resp.status_code, 302)

    def test_ac_02_3_wrong_current_password_rejected(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse('accounts:change_password'),
            {
                'current_password': 'WrongCurrentPassword',
                'new_password': 'NewValidPassword123',
                'confirm_password': 'NewValidPassword123',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/change_password.html')
        self.assertContains(response, 'Current password is incorrect.')
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('StudentPassword123'))

    def test_ac_02_3_correct_current_password_updates_successfully(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse('accounts:change_password'),
            {
                'current_password': 'StudentPassword123',
                'new_password': 'NewValidPassword123',
                'confirm_password': 'NewValidPassword123',
            },
            follow=True,
        )
        self.assertRedirects(response, reverse('accounts:dashboard'))
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('NewValidPassword123'))
        self.assertFalse(self.student.must_change_password)

    def test_ac_02_4_must_change_password_forces_redirect_before_dashboard(self):
        self.student.must_change_password = True
        self.student.save()

        login_resp = self.client.post(
            reverse('accounts:login'),
            {'username': 'student1', 'password': 'StudentPassword123'},
        )
        self.assertRedirects(login_resp, reverse('accounts:change_password'))

        dash_resp = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(dash_resp, reverse('accounts:change_password'))

        other_resp = self.client.get(reverse('hostel:student_announcements'))
        self.assertRedirects(other_resp, reverse('accounts:change_password'))

        change_resp = self.client.post(
            reverse('accounts:change_password'),
            {
                'current_password': 'StudentPassword123',
                'new_password': 'UpdatedPassword123',
                'confirm_password': 'UpdatedPassword123',
            },
            follow=True,
        )
        self.assertRedirects(change_resp, reverse('accounts:dashboard'))
        self.student.refresh_from_db()
        self.assertFalse(self.student.must_change_password)

    def test_ac_nfr_01_student_gets_403_on_warden_url_and_guard(self):
        self.client.force_login(self.student)
        warden_url_resp = self.client.get(reverse('hostel:warden_announcements'))
        self.assertEqual(warden_url_resp.status_code, 403)

        @warden_required
        def dummy_warden_view(request):
            return HttpResponse('ok')

        request = self.factory.get('/warden-only/')
        request.user = self.student
        self.assertEqual(dummy_warden_view(request).status_code, 403)

        @student_required
        def dummy_student_view(request):
            return HttpResponse('ok')

        warden_request = self.factory.get('/student-only/')
        warden_request.user = self.warden
        self.assertEqual(dummy_student_view(warden_request).status_code, 403)

    def test_ac_nfr_01_anonymous_user_redirects_to_login_on_dashboard(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}",
        )

    def test_logout_requires_post_and_clears_session(self):
        self.client.force_login(self.student)
        get_logout = self.client.get(reverse('accounts:logout'))
        self.assertEqual(get_logout.status_code, 405)

        post_logout = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(post_logout, '/')

        dash_after_logout = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(
            dash_after_logout,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}",
        )

    def test_create_warden_management_command(self):
        out = StringIO()
        call_command(
            'create_warden',
            '--username',
            'new_warden',
            '--password',
            'StrongWardenPass123',
            stdout=out,
        )
        created = User.objects.get(username='new_warden')
        self.assertEqual(created.role, 'warden')
        self.assertTrue(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertTrue(created.check_password('StrongWardenPass123'))

        with self.assertRaises(CommandError):
            call_command(
                'create_warden',
                '--username',
                'new_warden',
                '--password',
                'AnotherPass123',
            )


def make_warden(username='warden', password='warden-pass-123'):
    return User.objects.create_user(
        username=username,
        password=password,
        role='warden',
        is_staff=True,
    )


def make_student(username, student_id, full_name, password='student-pass-123'):
    user = User.objects.create_user(
        username=username,
        password=password,
        role='student',
        is_staff=False,
    )
    profile = StudentProfile.objects.create(
        user=user,
        student_id=student_id,
        full_name=full_name,
        contact_number='03001234567',
        guardian_name='Guardian Name',
        guardian_contact='03009876543',
        status='Active',
        room_number='101',
    )
    return user, profile


class StudentProfileTests(TestCase):

    def setUp(self):
        self.warden = make_warden()
        self.student1_user, self.student1_profile = make_student('ali', '25I-001', 'Ali Khan')
        self.student2_user, self.student2_profile = make_student('sara', '25I-002', 'Sara Ahmed')

    # AC-03.1: Student sees own profile
    def test_ac_03_1_student_sees_own_profile(self):
        self.client.force_login(self.student1_user)
        response = self.client.get(reverse('accounts:student_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ali Khan')
        self.assertContains(response, '25I-001')
        self.assertNotContains(response, 'Sara Ahmed')
        self.assertNotContains(response, '25I-002')

    # AC-03.1: Student dashboard shows own data only
    def test_ac_03_1_student_dashboard_shows_own_data(self):
        self.client.force_login(self.student1_user)
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ali Khan')
        self.assertNotContains(response, 'Sara Ahmed')

    # AC-03.2: Student cannot access warden announcement management page
    def test_ac_03_2_student_cannot_access_warden_announcements(self):
        self.client.force_login(self.student1_user)
        response = self.client.get(reverse('hostel:warden_announcements'))
        self.assertEqual(response.status_code, 403)

    # AC-03.2: Student cannot access warden menu management page
    def test_ac_03_2_student_cannot_access_warden_menu(self):
        self.client.force_login(self.student1_user)
        response = self.client.get(reverse('hostel:warden_menu'))
        self.assertEqual(response.status_code, 403)

    # AC-03.2: Student cannot access warden rules management page
    def test_ac_03_2_student_cannot_access_warden_rules(self):
        self.client.force_login(self.student1_user)
        response = self.client.get(reverse('hostel:warden_rules'))
        self.assertEqual(response.status_code, 403)

    # AC-NFR-01: Warden cannot access student dashboard
    def test_ac_nfr_01_warden_cannot_access_student_dashboard(self):
        self.client.force_login(self.warden)
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 403)

    # AC-NFR-01: Warden cannot access student profile page
    def test_ac_nfr_01_warden_cannot_access_student_profile(self):
        self.client.force_login(self.warden)
        response = self.client.get(reverse('accounts:student_profile'))
        self.assertEqual(response.status_code, 403)

    # Anonymous user redirected to login
    def test_anonymous_user_redirected_from_dashboard(self):
        response = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    # Anonymous user redirected from profile
    def test_anonymous_user_redirected_from_profile(self):
        response = self.client.get(reverse('accounts:student_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    # Student2 cannot see Student1 data (privacy isolation)
    def test_student2_cannot_see_student1_data(self):
        self.client.force_login(self.student2_user)
        response = self.client.get(reverse('accounts:student_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sara Ahmed')
        self.assertNotContains(response, 'Ali Khan')
        self.assertNotContains(response, '25I-001')

    # StudentProfile model: student_id must be unique
    def test_student_id_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            new_user = User.objects.create_user(
                username='duplicate',
                password='pass123',
                role='student',
                is_staff=False,
            )
            StudentProfile.objects.create(
                user=new_user,
                student_id='25I-001',
                full_name='Duplicate Student',
                contact_number='03001111111',
                guardian_name='Guardian',
                guardian_contact='03002222222',
            )

    # StudentProfile model: is_active() works correctly
    def test_student_is_active_method(self):
        self.assertTrue(self.student1_profile.is_active())
        self.student1_profile.status = 'Left'
        self.student1_profile.save()
        self.assertFalse(self.student1_profile.is_active())
