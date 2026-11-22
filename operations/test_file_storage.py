import shutil
import tempfile
import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from . import file_storage
from .models import StoredFile

User = get_user_model()

JPG_HEADER = b'\xff\xd8\xff\xe0'
PNG_HEADER = b'\x89PNG\r\n\x1a\n'
PDF_HEADER = b'%PDF-1.4\n'


class FileStorageServiceTests(TestCase):
    """Unit, EP, BVA, and authorization tests for VS-08 shared local file storage."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='hostelease_uploads_')
        self.override = override_settings(PRIVATE_UPLOAD_ROOT=Path(self.temp_dir))
        self.override.enable()

        self.warden = User.objects.create_user(
            username='warden_fs', password='WardenPassword123!', role='warden', is_staff=True
        )
        self.student1 = User.objects.create_user(
            username='stu_fs_1', password='StudentPassword123!', role='student'
        )
        self.student2 = User.objects.create_user(
            username='stu_fs_2', password='StudentPassword123!', role='student'
        )

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_jpg_png_pdf_saved_to_filesystem_and_db(self):
        samples = [
            ('receipt.jpg', JPG_HEADER + b'data', 'image/jpeg'),
            ('receipt.jpeg', JPG_HEADER + b'data', 'image/jpeg'),
            ('photo.png', PNG_HEADER + b'data', 'image/png'),
            ('slip.pdf', PDF_HEADER + b'data', 'application/pdf'),
        ]
        for filename, content, expected_ct in samples:
            upload = SimpleUploadedFile(filename, content, content_type=expected_ct)
            record = file_storage.save_uploaded_file(
                upload,
                category=StoredFile.CATEGORY_PAYMENT_PROOF,
                owner_user_id=self.student1.pk,
                record_ref='proof-1',
            )
            self.assertEqual(record.content_type, expected_ct)
            self.assertEqual(record.size_bytes, len(content))
            self.assertEqual(record.record_ref, 'proof-1')
            disk_path = file_storage.resolve_stored_path(record)
            self.assertTrue(disk_path.is_file())
            self.assertEqual(disk_path.read_bytes(), content)

    def test_path_traversal_filename_is_sanitized_to_uuid(self):
        upload = SimpleUploadedFile('../../etc/passwd.pdf', PDF_HEADER + b'123', content_type='application/pdf')
        record = file_storage.save_uploaded_file(
            upload,
            category=StoredFile.CATEGORY_COMPLAINT_ATTACHMENT,
            owner_user_id=self.student1.pk,
        )
        self.assertNotIn('..', record.relative_path)
        self.assertTrue(record.relative_path.startswith('complaint_attachment/'))
        self.assertTrue(record.relative_path.endswith('.pdf'))

    def test_size_boundaries_bva(self):
        # 0 bytes -> rejected
        empty = SimpleUploadedFile('empty.pdf', b'', content_type='application/pdf')
        with self.assertRaises(file_storage.FileTooLargeError):
            file_storage.save_uploaded_file(
                empty, category=StoredFile.CATEGORY_PAYMENT_PROOF, owner_user_id=self.student1.pk
            )

        # Exact 5 MB -> accepted
        exact_5mb = PDF_HEADER + b'a' * (file_storage.MAX_FILE_SIZE_BYTES - len(PDF_HEADER))
        exact_upload = SimpleUploadedFile('exact.pdf', exact_5mb, content_type='application/pdf')
        record = file_storage.save_uploaded_file(
            exact_upload, category=StoredFile.CATEGORY_PAYMENT_PROOF, owner_user_id=self.student1.pk
        )
        self.assertEqual(record.size_bytes, file_storage.MAX_FILE_SIZE_BYTES)

        # 5 MB + 1 byte -> rejected
        over_5mb = PDF_HEADER + b'a' * (file_storage.MAX_FILE_SIZE_BYTES - len(PDF_HEADER) + 1)
        over_upload = SimpleUploadedFile('over.pdf', over_5mb, content_type='application/pdf')
        with self.assertRaises(file_storage.FileTooLargeError):
            file_storage.save_uploaded_file(
                over_upload, category=StoredFile.CATEGORY_PAYMENT_PROOF, owner_user_id=self.student1.pk
            )

    def test_invalid_extensions_and_spoofed_content_rejected(self):
        for name, content in [
            ('script.exe', b'MZ\x90\x00'),
            ('notes.txt', b'hello world'),
            ('image.gif', b'GIF89a'),
            ('fake.pdf', b'not really a pdf'),
            ('fake.jpg', b'plain text'),
            ('fake.png', b'plain text'),
        ]:
            upload = SimpleUploadedFile(name, content)
            with self.assertRaises(file_storage.InvalidFileTypeError, msg=name):
                file_storage.save_uploaded_file(
                    upload, category=StoredFile.CATEGORY_PAYMENT_PROOF, owner_user_id=self.student1.pk
                )

    def test_invalid_category_rejected(self):
        upload = SimpleUploadedFile('a.pdf', PDF_HEADER + b'ok')
        with self.assertRaises(file_storage.FileStorageError):
            file_storage.save_uploaded_file(upload, category='other', owner_user_id=self.student1.pk)

    def test_stored_file_record_cannot_be_hard_deleted(self):
        upload = SimpleUploadedFile('a.pdf', PDF_HEADER + b'ok')
        record = file_storage.save_uploaded_file(
            upload, category=StoredFile.CATEGORY_PAYMENT_PROOF, owner_user_id=self.student1.pk
        )
        with self.assertRaises(PermissionError):
            record.delete()

    def test_file_delivery_authorization_and_path_isolation(self):
        upload = SimpleUploadedFile('proof.png', PNG_HEADER + b'secret-bytes', content_type='image/png')
        record = file_storage.save_uploaded_file(
            upload, category=StoredFile.CATEGORY_PAYMENT_PROOF, owner_user_id=self.student1.pk
        )
        url = reverse('operations:download_file', args=[record.file_key])

        # Anonymous -> redirected to login
        anon_resp = self.client.get(url)
        self.assertEqual(anon_resp.status_code, 302)

        # Other student -> 403 Forbidden
        self.client.force_login(self.student2)
        other_resp = self.client.get(url)
        self.assertEqual(other_resp.status_code, 403)

        # Owner student -> 200 OK with exact bytes
        self.client.force_login(self.student1)
        owner_resp = self.client.get(url)
        self.assertEqual(owner_resp.status_code, 200)
        self.assertEqual(b''.join(owner_resp.streaming_content), PNG_HEADER + b'secret-bytes')

        # Warden -> 200 OK
        self.client.force_login(self.warden)
        warden_resp = self.client.get(url)
        self.assertEqual(warden_resp.status_code, 200)
        self.assertEqual(b''.join(warden_resp.streaming_content), PNG_HEADER + b'secret-bytes')

        # Guessed / non-existent UUID -> 404
        missing_url = reverse('operations:download_file', args=[uuid.uuid4()])
        self.assertEqual(self.client.get(missing_url).status_code, 404)

        # Guessing /media/<relative_path> does not expose private uploads
        self.assertEqual(self.client.get(f'/media/{record.relative_path}').status_code, 404)
