import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from hostel.models import Student
from operations import file_storage
from operations.models import StoredFile

from . import services
from .models import Payment

User = get_user_model()

PDF_HEADER = b'%PDF-1.4\n'
PNG_HEADER = b'\x89PNG\r\n\x1a\n'


class PaymentProofSubmissionTests(TestCase):
    """Functional, Negative, EP, BVA, and isolation tests for VS-09."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='hostelease_vs09_')
        self.override = override_settings(PRIVATE_UPLOAD_ROOT=Path(self.temp_dir))
        self.override.enable()

        self.warden = User.objects.create_user(
            username='warden_vs09', password='WardenPassword123!', role='warden', is_staff=True
        )
        self.user1 = User.objects.create_user(
            username='S-901', password='StudentPassword123!', role='student'
        )
        self.student1 = Student.objects.create(
            student_id='S-901',
            full_name='Zara Khan',
            contact_number='03001234567',
            guardian_name='Khan',
            guardian_contact_number='03007654321',
            user_id=self.user1.pk,
        )
        services.create_fee_record(self.student1.pk, '20000', '5000')

        self.user2 = User.objects.create_user(
            username='S-902', password='StudentPassword123!', role='student'
        )
        self.student2 = Student.objects.create(
            student_id='S-902',
            full_name='Bilal Ali',
            contact_number='03011234567',
            guardian_name='Ali',
            guardian_contact_number='03017654321',
            user_id=self.user2.pk,
        )
        services.create_fee_record(self.student2.pk, '15000', '0')

        self.url = reverse('finance_student:my_fees')

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ac_04_1_valid_proof_submission_creates_pending_record_without_changing_paid(self):
        self.client.force_login(self.user1)
        upload = SimpleUploadedFile('bank_slip.pdf', PDF_HEADER + b'proof-bytes', content_type='application/pdf')
        resp = self.client.post(
            self.url,
            {'amount': '7500.00', 'payment_date': '2026-11-22', 'proof_file': upload},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Pending')
        self.assertContains(resp, '7500.00')

        # Pending proof appears in pending interface & does NOT alter paid_amount
        pending = services.list_pending_payments()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].amount, Decimal('7500.00'))
        self.assertEqual(pending[0].status, Payment.STATUS_PENDING)
        self.assertEqual(services.count_pending_payments(), 1)

        ledger = services.get_ledger(self.student1.pk)
        self.assertEqual(ledger['paid_amount'], Decimal('5000.00'))
        self.assertEqual(ledger['remaining_amount'], Decimal('15000.00'))

        # File stored locally via VS-08 and accessible by owner
        stored = StoredFile.objects.get(file_key=pending[0].proof_file_key)
        self.assertTrue(file_storage.resolve_stored_path(stored).is_file())

    def test_ac_04_2_invalid_file_type_or_oversized_rejected_with_no_record(self):
        self.client.force_login(self.user1)
        before_payments = Payment.objects.count()

        # Invalid extension
        bad_ext = SimpleUploadedFile('malware.exe', b'MZ\x90\x00')
        resp = self.client.post(
            self.url,
            {'amount': '1000', 'payment_date': '2026-11-22', 'proof_file': bad_ext},
        )
        self.assertContains(resp, 'Only JPG, PNG, and PDF')
        self.assertEqual(Payment.objects.count(), before_payments)
        self.assertEqual(StoredFile.objects.count(), 0)

        # Oversized (> 5 MB)
        over_5mb = PDF_HEADER + b'x' * (file_storage.MAX_FILE_SIZE_BYTES - len(PDF_HEADER) + 1)
        big_file = SimpleUploadedFile('big.pdf', over_5mb, content_type='application/pdf')
        resp2 = self.client.post(
            self.url,
            {'amount': '1000', 'payment_date': '2026-11-22', 'proof_file': big_file},
        )
        self.assertContains(resp2, '5 MB')
        self.assertEqual(Payment.objects.count(), before_payments)
        self.assertEqual(StoredFile.objects.count(), 0)

    def test_invalid_amount_and_date_rejected(self):
        self.client.force_login(self.user1)
        for bad_amount in ('0', '-100', 'abc', ''):
            upload = SimpleUploadedFile('slip.png', PNG_HEADER + b'ok', content_type='image/png')
            resp = self.client.post(
                self.url,
                {'amount': bad_amount, 'payment_date': '2026-11-22', 'proof_file': upload},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(StoredFile.objects.count(), 0)

        upload = SimpleUploadedFile('slip.png', PNG_HEADER + b'ok', content_type='image/png')
        resp = self.client.post(
            self.url,
            {'amount': '500', 'payment_date': 'not-a-date', 'proof_file': upload},
        )
        self.assertContains(resp, 'valid date')
        self.assertEqual(StoredFile.objects.count(), 0)

    def test_multiple_pending_proofs_and_above_remaining_allowed_oq20(self):
        self.client.force_login(self.user1)
        for amt in ('10000', '20000'):
            upload = SimpleUploadedFile('slip.png', PNG_HEADER + b'ok', content_type='image/png')
            self.client.post(self.url, {'amount': amt, 'payment_date': '2026-11-22', 'proof_file': upload})
        self.assertEqual(services.count_pending_payments(), 2)
        self.assertEqual(services.get_ledger(self.student1.pk)['paid_amount'], Decimal('5000.00'))

    def test_student_sees_only_own_proofs_and_cannot_access_other_student_file(self):
        # Student 1 submits a proof
        self.client.force_login(self.user1)
        upload = SimpleUploadedFile('s1_proof.png', PNG_HEADER + b's1-secret', content_type='image/png')
        self.client.post(self.url, {'amount': '3333', 'payment_date': '2026-11-22', 'proof_file': upload})
        s1_payment = Payment.objects.filter(student_ref=self.student1.pk, source=Payment.SOURCE_PROOF).first()

        # Student 2 does not see Student 1's proof and gets 403 on its file download URL
        self.client.force_login(self.user2)
        s2_page = self.client.get(self.url)
        self.assertNotContains(s2_page, '3333')
        self.assertNotContains(s2_page, 's1_proof.png')
        file_url = reverse('operations:download_file', args=[s1_payment.proof_file_key])
        self.assertEqual(self.client.get(file_url).status_code, 403)

    def test_role_boundaries_for_student_fee_route(self):
        # Anonymous -> 302
        self.assertEqual(self.client.get(self.url).status_code, 302)
        # Warden -> 403
        self.client.force_login(self.warden)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_payment_record_cannot_be_hard_deleted(self):
        p = Payment.objects.filter(student_ref=self.student1.pk).first()
        with self.assertRaises(PermissionError):
            p.delete()
