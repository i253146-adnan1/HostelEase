"""Tests for VS-22: User Display Picture (Profile Avatar)."""

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

User = get_user_model()


def _make_image_file(name='avatar.png', fmt='PNG', color=(37, 99, 235), size=(64, 64), content_type='image/png'):
    buf = BytesIO()
    img = Image.new('RGB', size, color=color)
    img.save(buf, format=fmt)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type=content_type)


class UserAvatarVS22Tests(TestCase):
    def setUp(self):
        self.temp_media_dir = tempfile.mkdtemp(prefix='hostelease_test_media_')
        self.addCleanup(lambda: shutil.rmtree(self.temp_media_dir, ignore_errors=True))

        self.warden = User.objects.create_user(
            username='warden_dp',
            password='WardenPassword123',
            role='warden',
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username='student_dp',
            password='StudentPassword123',
            role='student',
            student_id='STU-DP-01',
        )

    def test_unauthenticated_requests_redirect_302(self):
        settings_resp = self.client.get(reverse('accounts:avatar_settings'))
        upload_resp = self.client.post(reverse('accounts:avatar_upload'))
        remove_resp = self.client.post(reverse('accounts:avatar_remove'))

        self.assertEqual(settings_resp.status_code, 302)
        self.assertEqual(upload_resp.status_code, 302)
        self.assertEqual(remove_resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), settings_resp['Location'])

    def test_student_upload_replace_and_remove_with_file_cleanup(self):
        with override_settings(MEDIA_ROOT=self.temp_media_dir):
            self.client.force_login(self.student)

            # Upload initial PNG
            img1 = _make_image_file('first.png', fmt='PNG', content_type='image/png')
            resp1 = self.client.post(reverse('accounts:avatar_upload'), {'avatar': img1}, follow=True)
            self.assertEqual(resp1.status_code, 200)
            self.student.refresh_from_db()
            self.assertTrue(bool(self.student.avatar))
            first_name = self.student.avatar.name
            self.assertTrue(first_name.startswith('avatars/'))
            self.assertTrue(self.student.avatar.storage.exists(first_name))

            # Replace with WEBP and verify old file is deleted
            img2 = _make_image_file('second.webp', fmt='WEBP', content_type='image/webp')
            resp2 = self.client.post(reverse('accounts:avatar_upload'), {'avatar': img2}, follow=True)
            self.assertEqual(resp2.status_code, 200)
            self.student.refresh_from_db()
            second_name = self.student.avatar.name
            self.assertNotEqual(first_name, second_name)
            self.assertFalse(self.student.avatar.storage.exists(first_name))
            self.assertTrue(self.student.avatar.storage.exists(second_name))

            # Remove and verify file is deleted
            resp3 = self.client.post(reverse('accounts:avatar_remove'), follow=True)
            self.assertEqual(resp3.status_code, 200)
            self.student.refresh_from_db()
            self.assertFalse(bool(self.student.avatar))
            self.assertFalse(self.student._meta.get_field('avatar').storage.exists(second_name))

    def test_warden_upload_replace_and_remove(self):
        with override_settings(MEDIA_ROOT=self.temp_media_dir):
            self.client.force_login(self.warden)

            img1 = _make_image_file('warden1.jpg', fmt='JPEG', content_type='image/jpeg')
            resp1 = self.client.post(reverse('accounts:avatar_upload'), {'avatar': img1}, follow=True)
            self.assertEqual(resp1.status_code, 200)
            self.warden.refresh_from_db()
            first_name = self.warden.avatar.name
            self.assertTrue(self.warden.avatar.storage.exists(first_name))

            img2 = _make_image_file('warden2.png', fmt='PNG', content_type='image/png')
            resp2 = self.client.post(reverse('accounts:avatar_upload'), {'avatar': img2}, follow=True)
            self.assertEqual(resp2.status_code, 200)
            self.warden.refresh_from_db()
            second_name = self.warden.avatar.name
            self.assertFalse(self.warden.avatar.storage.exists(first_name))
            self.assertTrue(self.warden.avatar.storage.exists(second_name))

            resp3 = self.client.post(reverse('accounts:avatar_remove'), follow=True)
            self.assertEqual(resp3.status_code, 200)
            self.warden.refresh_from_db()
            self.assertFalse(bool(self.warden.avatar))
            self.assertFalse(self.warden._meta.get_field('avatar').storage.exists(second_name))

    def test_invalid_file_type_and_oversized_file_rejected_without_corrupting_existing(self):
        with override_settings(MEDIA_ROOT=self.temp_media_dir):
            self.client.force_login(self.student)

            # Set a valid existing DP first
            valid_img = _make_image_file('valid.png', fmt='PNG', content_type='image/png')
            self.client.post(reverse('accounts:avatar_upload'), {'avatar': valid_img})
            self.student.refresh_from_db()
            existing_name = self.student.avatar.name

            # 1. Invalid extension (.txt)
            txt_file = SimpleUploadedFile('notes.txt', b'not an image', content_type='text/plain')
            resp_txt = self.client.post(reverse('accounts:avatar_upload'), {'avatar': txt_file})
            self.assertEqual(resp_txt.status_code, 200)
            self.assertContains(resp_txt, 'Unsupported file format')
            self.student.refresh_from_db()
            self.assertEqual(self.student.avatar.name, existing_name)

            # 2. Disguised non-image with .png extension
            fake_png = SimpleUploadedFile('malware.png', b'MZ\x90\x00not_a_real_png', content_type='image/png')
            resp_fake = self.client.post(reverse('accounts:avatar_upload'), {'avatar': fake_png})
            self.assertEqual(resp_fake.status_code, 200)
            self.assertContains(resp_fake, 'not a valid image')
            self.student.refresh_from_db()
            self.assertEqual(self.student.avatar.name, existing_name)

            # 3. Oversized (> 2 MB)
            big_bytes = b'x' * (2 * 1024 * 1024 + 1)
            big_file = SimpleUploadedFile('huge.jpg', big_bytes, content_type='image/jpeg')
            resp_big = self.client.post(reverse('accounts:avatar_upload'), {'avatar': big_file})
            self.assertEqual(resp_big.status_code, 200)
            self.assertContains(resp_big, 'exceeds the 2 MB limit')
            self.student.refresh_from_db()
            self.assertEqual(self.student.avatar.name, existing_name)
            self.assertTrue(self.student.avatar.storage.exists(existing_name))

    def test_dashboard_and_base_render_with_and_without_avatar(self):
        with override_settings(MEDIA_ROOT=self.temp_media_dir):
            self.client.force_login(self.student)

            # Without avatar -> initials fallback rendered
            dash_no_avatar = self.client.get(reverse('accounts:dashboard'))
            self.assertEqual(dash_no_avatar.status_code, 200)
            self.assertContains(dash_no_avatar, 'class="he-user-avatar-initials"')
            self.assertNotContains(dash_no_avatar, 'class="he-user-avatar-img"')

            # Upload avatar -> circular image thumbnail rendered in base.html & dashboard
            img = _make_image_file('student_thumb.png', fmt='PNG', content_type='image/png')
            self.client.post(reverse('accounts:avatar_upload'), {'avatar': img})
            self.student.refresh_from_db()

            dash_with_avatar = self.client.get(reverse('accounts:dashboard'))
            self.assertEqual(dash_with_avatar.status_code, 200)
            self.assertContains(dash_with_avatar, 'class="he-user-avatar-img"')
            self.assertContains(dash_with_avatar, self.student.avatar.url)

            # Warden dashboard also renders own avatar independently
            self.client.force_login(self.warden)
            warden_dash = self.client.get(reverse('accounts:dashboard'))
            self.assertEqual(warden_dash.status_code, 200)
            self.assertContains(warden_dash, 'class="he-user-avatar-initials"')
            self.assertNotContains(warden_dash, 'class="he-user-avatar-img"')
            self.assertNotContains(warden_dash, self.student.avatar.url)
