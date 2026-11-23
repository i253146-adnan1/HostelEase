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


class PaymentVerificationTests(TestCase):
    """Automated tests for VS-12: Warden payment verification/rejection.

    Traceability:
    - FR-05: Warden pending proof list (AC-05.1).
    - FR-06: Warden verify or reject with required remark (AC-05.1, AC-05.2).
    - NFR-02: Consistent ledger invariants on verification.
    - BR-03: Only verified proofs update ledger totals; rejected proofs preserve totals.
    - EC-37: Idempotency; double decisions prevented.
    - NFR-01: Role isolation; student direct URL access returns HTTP 403.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='hostelease_vs12_')
        self.override = override_settings(PRIVATE_UPLOAD_ROOT=Path(self.temp_dir))
        self.override.enable()

        self.warden = User.objects.create_user(
            username='warden_vs12', password='WardenPassword123!', role='warden', is_staff=True
        )
        self.student_user = User.objects.create_user(
            username='S-1201', password='StudentPassword123!', role='student'
        )
        self.student = Student.objects.create(
            student_id='S-1201',
            full_name='Tariq Mehmood',
            contact_number='03009876543',
            guardian_name='Mehmood',
            guardian_contact_number='03001234567',
            user_id=self.student_user.pk,
        )
        services.create_fee_record(self.student.pk, '25000.00', '5000.00')

        # Create a pending payment proof via service
        upload = SimpleUploadedFile('bank_challan.pdf', PDF_HEADER + b'sample-proof', content_type='application/pdf')
        self.payment = services.submit_payment_proof(
            student_ref=self.student.pk,
            owner_user_id=self.student_user.pk,
            amount='10000.00',
            payment_date='2026-11-20',
            proof_file=upload,
        )

        self.pending_url = reverse('finance:pending_payments')
        self.verify_url = reverse('finance:verify_payment', kwargs={'payment_id': self.payment.pk})
        self.reject_url = reverse('finance:reject_payment', kwargs={'payment_id': self.payment.pk})

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # --- FR-05 & UI Tests ---

    def test_warden_sees_pending_payment_in_pending_list(self):
        self.client.force_login(self.warden)
        resp = self.client.get(self.pending_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Tariq Mehmood')
        self.assertContains(resp, 'S-1201')
        self.assertContains(resp, '10000.00')
        self.assertContains(resp, 'View Proof')
        self.assertContains(resp, self.verify_url)
        self.assertContains(resp, self.reject_url)

    def test_warden_fee_detail_shows_pending_payment_with_actions(self):
        self.client.force_login(self.warden)
        resp = self.client.get(reverse('finance:detail', kwargs={'student_pk': self.student.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '10000.00')
        self.assertContains(resp, 'Pending')
        self.assertContains(resp, self.verify_url)

    # --- AC-05.1 & NFR-02: Verification Tests ---

    def test_ac_05_1_verify_pending_payment_via_service(self):
        initial_ledger = services.get_ledger(self.student.pk)
        self.assertEqual(initial_ledger['paid_amount'], Decimal('5000.00'))
        self.assertEqual(initial_ledger['remaining_amount'], Decimal('20000.00'))
        self.assertEqual(initial_ledger['excess_paid'], Decimal('0.00'))

        verified = services.verify_payment(self.payment.pk, warden_username=self.warden.username)
        self.payment.refresh_from_db()

        self.assertEqual(self.payment.status, Payment.STATUS_VERIFIED)
        self.assertIsNotNone(self.payment.decided_at)
        self.assertEqual(self.payment.decided_by, self.warden.username)

        updated_ledger = services.get_ledger(self.student.pk)
        # Invariants (NFR-02): paid = 5000 + 10000 = 15000
        self.assertEqual(updated_ledger['paid_amount'], Decimal('15000.00'))
        self.assertEqual(updated_ledger['remaining_amount'], Decimal('10000.00'))
        self.assertEqual(updated_ledger['excess_paid'], Decimal('0.00'))

    def test_ac_05_1_verify_pending_payment_via_post_view(self):
        self.client.force_login(self.warden)
        resp = self.client.post(self.verify_url)
        self.assertRedirects(resp, self.pending_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_VERIFIED)
        self.assertEqual(self.payment.decided_by, self.warden.username)

        ledger = services.get_ledger(self.student.pk)
        self.assertEqual(ledger['paid_amount'], Decimal('15000.00'))
        self.assertEqual(ledger['remaining_amount'], Decimal('10000.00'))

        # Once verified, it is removed from the pending list
        resp2 = self.client.get(self.pending_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertNotContains(resp2, f'#{self.payment.pk}')

    def test_ac_05_1_verify_overpayment_sets_excess_paid(self):
        """When verified payment exceeds remaining fee, excess_paid is calculated (NFR-02, BR-10)."""
        upload = SimpleUploadedFile('extra_proof.pdf', PDF_HEADER + b'extra', content_type='application/pdf')
        large_payment = services.submit_payment_proof(
            student_ref=self.student.pk,
            owner_user_id=self.student_user.pk,
            amount='25000.00',  # 5000 already paid + 25000 = 30000 on 25000 total fee
            payment_date='2026-11-21',
            proof_file=upload,
        )
        services.verify_payment(large_payment.pk, warden_username='warden_vs12')
        ledger = services.get_ledger(self.student.pk)
        self.assertEqual(ledger['paid_amount'], Decimal('30000.00'))
        self.assertEqual(ledger['remaining_amount'], Decimal('0.00'))
        self.assertEqual(ledger['excess_paid'], Decimal('5000.00'))

    # --- AC-05.2: Rejection Tests ---

    def test_ac_05_2_reject_with_remark_via_service_preserves_ledger(self):
        initial_ledger = services.get_ledger(self.student.pk)

        rejected = services.reject_payment(
            self.payment.pk,
            remark='Slip amount does not match bank transaction record.',
            warden_username=self.warden.username,
        )
        self.payment.refresh_from_db()

        self.assertEqual(self.payment.status, Payment.STATUS_REJECTED)
        self.assertEqual(self.payment.warden_remark, 'Slip amount does not match bank transaction record.')
        self.assertEqual(self.payment.rejection_remark, 'Slip amount does not match bank transaction record.')
        self.assertIsNotNone(self.payment.decided_at)
        self.assertEqual(self.payment.decided_by, self.warden.username)

        # Balances remain untouched
        after_ledger = services.get_ledger(self.student.pk)
        self.assertEqual(after_ledger['paid_amount'], initial_ledger['paid_amount'])
        self.assertEqual(after_ledger['remaining_amount'], initial_ledger['remaining_amount'])
        self.assertEqual(after_ledger['excess_paid'], initial_ledger['excess_paid'])

    def test_ac_05_2_reject_with_remark_via_post_view(self):
        self.client.force_login(self.warden)
        remark = 'Invalid bank stamp; please re-upload clear photo.'
        resp = self.client.post(self.reject_url, {'remark': remark})
        self.assertRedirects(resp, self.pending_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_REJECTED)
        self.assertEqual(self.payment.warden_remark, remark)

        # Student fee view reflects the rejection remark (AC-05.2)
        self.client.force_login(self.student_user)
        student_resp = self.client.get(reverse('finance_student:my_fees'))
        self.assertEqual(student_resp.status_code, 200)
        self.assertContains(student_resp, 'Rejected')
        self.assertContains(student_resp, remark)

    def test_ac_05_2_reject_without_remark_raises_error(self):
        """Rejection requires a non-empty remark (FR-06, AC-05.2)."""
        with self.assertRaises(services.FeeError) as ctx:
            services.reject_payment(self.payment.pk, remark='')
        self.assertIn('A rejection remark is required', str(ctx.exception))

        with self.assertRaises(services.FeeError) as ctx2:
            services.reject_payment(self.payment.pk, remark='   ')
        self.assertIn('A rejection remark is required', str(ctx2.exception))

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PENDING)

    def test_ac_05_2_reject_without_remark_in_view_leaves_pending(self):
        self.client.force_login(self.warden)
        resp = self.client.post(self.reject_url, {'remark': '  '})
        self.assertRedirects(resp, self.pending_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PENDING)

    # --- EC-37: Idempotency & State Transition Tests ---

    def test_ec_37_double_verify_prevented(self):
        """Only pending proofs can be decided; repeated decisions raise error and prevent double-counting."""
        services.verify_payment(self.payment.pk, warden_username='warden1')
        ledger_first = services.get_ledger(self.student.pk)
        self.assertEqual(ledger_first['paid_amount'], Decimal('15000.00'))

        with self.assertRaises(services.FeeError) as ctx:
            services.verify_payment(self.payment.pk, warden_username='warden1')
        self.assertIn('already been reviewed', str(ctx.exception))

        # Ledger amount must NOT have been double-added
        ledger_second = services.get_ledger(self.student.pk)
        self.assertEqual(ledger_second['paid_amount'], Decimal('15000.00'))

    def test_ec_37_cannot_verify_rejected_payment(self):
        services.reject_payment(self.payment.pk, remark='Fake proof', warden_username='warden1')
        with self.assertRaises(services.FeeError) as ctx:
            services.verify_payment(self.payment.pk, warden_username='warden1')
        self.assertIn('already been reviewed', str(ctx.exception))

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_REJECTED)

    def test_ec_37_cannot_reject_verified_payment(self):
        services.verify_payment(self.payment.pk, warden_username='warden1')
        with self.assertRaises(services.FeeError) as ctx:
            services.reject_payment(self.payment.pk, remark='Changed mind', warden_username='warden1')
        self.assertIn('already been reviewed', str(ctx.exception))

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_VERIFIED)

    def test_decision_on_nonexistent_payment_raises_error(self):
        with self.assertRaises(services.FeeError):
            services.verify_payment(99999)
        with self.assertRaises(services.FeeError):
            services.reject_payment(99999, remark='Does not exist')

    # --- NFR-01: Role-Based Access Control Guards ---

    def test_nfr_01_student_cannot_access_pending_payments(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.pending_url)
        self.assertEqual(resp.status_code, 403)

    def test_nfr_01_student_cannot_verify_payment(self):
        self.client.force_login(self.student_user)
        resp = self.client.post(self.verify_url)
        self.assertEqual(resp.status_code, 403)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PENDING)

    def test_nfr_01_student_cannot_reject_payment(self):
        self.client.force_login(self.student_user)
        resp = self.client.post(self.reject_url, {'remark': 'Hacked remark'})
        self.assertEqual(resp.status_code, 403)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.STATUS_PENDING)

    def test_nfr_01_anonymous_user_redirected_to_login(self):
        self.client.logout()
        resp_list = self.client.get(self.pending_url)
        self.assertEqual(resp_list.status_code, 302)
        self.assertIn('/accounts/login/', resp_list.url)

        resp_verify = self.client.post(self.verify_url)
        self.assertEqual(resp_verify.status_code, 302)

        resp_reject = self.client.post(self.reject_url, {'remark': 'Anon'})
        self.assertEqual(resp_reject.status_code, 302)
