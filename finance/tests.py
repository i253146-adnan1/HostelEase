from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from . import services
from .models import FeeChange, Payment

D = Decimal
User = get_user_model()


class LedgerTests(TestCase):
    """EP/BVA over zero, underpaid, exact-paid and excess-paid (AC-06.x, AC-NFR-02)."""

    def ledger(self, total, paid_verified=0):
        services.create_fee_record(1, total, paid_verified)
        return services.get_ledger(1)

    def test_zero_paid(self):
        l = self.ledger('1000')
        self.assertEqual((l['paid_amount'], l['remaining_amount'], l['excess_paid']), (D('0'), D('1000'), D('0')))

    def test_underpaid(self):
        l = self.ledger('1000', '400')
        self.assertEqual((l['paid_amount'], l['remaining_amount'], l['excess_paid']), (D('400'), D('600'), D('0')))

    def test_one_below_exact(self):
        l = self.ledger('1000', '999.99')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0.01'), D('0')))

    def test_exact_paid(self):
        l = self.ledger('1000', '1000')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0'), D('0')))

    def test_one_above_exact_is_excess(self):
        l = self.ledger('1000', '1000.01')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0'), D('0.01')))

    def test_excess_paid(self):
        l = self.ledger('1000', '1500')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0'), D('500')))

    def test_zero_total_fee_allowed(self):
        l = self.ledger('0')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0'), D('0')))

    def test_pending_and_rejected_do_not_affect_paid(self):
        services.create_fee_record(1, '1000')
        services.add_payment(1, '300', Payment.STATUS_PENDING)
        services.add_payment(1, '200', Payment.STATUS_REJECTED)
        self.assertEqual(services.get_ledger(1)['paid_amount'], D('0'))
        services.add_payment(1, '250', Payment.STATUS_VERIFIED)
        l = services.get_ledger(1)
        self.assertEqual((l['paid_amount'], l['remaining_amount']), (D('250'), D('750')))

    def test_multiple_verified_payments_sum(self):
        services.create_fee_record(1, '1000', '100')
        services.add_payment(1, '150', Payment.STATUS_VERIFIED)
        self.assertEqual(services.get_ledger(1)['paid_amount'], D('250'))

    def test_ledger_missing_returns_none(self):
        self.assertIsNone(services.get_ledger(404))

    def test_ledgers_are_per_student(self):
        services.create_fee_record(1, '1000', '100')
        services.create_fee_record(2, '500')
        self.assertEqual(services.get_ledger(2)['paid_amount'], D('0'))

    def test_duplicate_fee_record_rejected(self):
        services.create_fee_record(1, '1000')
        with self.assertRaises(services.FeeError):
            services.create_fee_record(1, '2000')

    def test_invalid_amounts_rejected(self):
        for bad in ('', 'abc', '-1', '10.555', 'NaN', 'Infinity', '100000000'):
            with self.assertRaises(services.FeeError, msg=bad):
                services.create_fee_record(9, bad)
        self.assertIsNone(services.get_ledger(9))

    def test_invalid_opening_paid_rejected_atomically(self):
        with self.assertRaises(services.FeeError):
            services.create_fee_record(1, '1000', '-5')
        self.assertIsNone(services.get_ledger(1))

    def test_max_amount_boundary(self):
        services.create_fee_record(1, '99999999.99')
        self.assertEqual(services.get_ledger(1)['total_fee'], D('99999999.99'))

    def test_non_positive_payment_rejected(self):
        with self.assertRaises(services.FeeError):
            services.add_payment(1, '0')

    def test_invalid_payment_status_rejected(self):
        with self.assertRaises(services.FeeError):
            services.add_payment(1, '5', 'Bogus')


class FeeChangeTests(TestCase):
    def setUp(self):
        services.create_fee_record(1, '1000', '600')

    def test_initial_history_row(self):
        h = services.get_history(1)
        self.assertEqual(len(h), 1)
        self.assertIsNone(h[0]['old_total'])
        self.assertEqual(h[0]['new_total'], D('1000'))

    def test_raise_total_without_reason(self):
        l = services.update_total_fee(1, '1200', '', 'warden')
        self.assertEqual((l['total_fee'], l['remaining_amount']), (D('1200'), D('600')))

    def test_history_records_old_new_reason_date_user(self):
        services.update_total_fee(1, '1200', 'Hostel fee increase', 'warden')
        top = services.get_history(1)[0]
        self.assertEqual((top['old_total'], top['new_total'], top['reason'], top['changed_by']),
                         (D('1000'), D('1200'), 'Hostel fee increase', 'warden'))
        self.assertIsNotNone(top['changed_at'])

    def test_lower_above_paid_without_reason_allowed(self):
        l = services.update_total_fee(1, '700')
        self.assertEqual(l['total_fee'], D('700'))

    def test_lower_to_exactly_paid_without_reason_allowed(self):
        l = services.update_total_fee(1, '600')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0'), D('0')))

    def test_lower_below_paid_without_reason_rejected(self):
        with self.assertRaises(services.FeeError):
            services.update_total_fee(1, '599.99')
        self.assertEqual(services.get_ledger(1)['total_fee'], D('1000'))
        self.assertEqual(len(services.get_history(1)), 1)

    def test_lower_below_paid_whitespace_reason_rejected(self):
        with self.assertRaises(services.FeeError):
            services.update_total_fee(1, '500', '   ')

    def test_lower_below_paid_with_reason_creates_excess(self):
        l = services.update_total_fee(1, '500', 'Scholarship granted', 'warden')
        self.assertEqual((l['remaining_amount'], l['excess_paid']), (D('0'), D('100')))
        self.assertEqual(services.get_history(1)[0]['reason'], 'Scholarship granted')

    def test_unchanged_total_rejected(self):
        with self.assertRaises(services.FeeError):
            services.update_total_fee(1, '1000')

    def test_negative_or_invalid_total_rejected(self):
        for bad in ('-1', 'x', ''):
            with self.assertRaises(services.FeeError):
                services.update_total_fee(1, bad, 'r')

    def test_unknown_student_rejected(self):
        with self.assertRaises(services.FeeError):
            services.update_total_fee(777, '10')

    def test_payment_history_untouched_by_fee_change(self):
        before = list(Payment.objects.values_list('id', 'amount', 'status'))
        services.update_total_fee(1, '100', 'Correction')
        self.assertEqual(before, list(Payment.objects.values_list('id', 'amount', 'status')))

    def test_pending_proof_amount_unchanged_by_fee_change(self):
        services.add_payment(1, '300', Payment.STATUS_PENDING)
        services.update_total_fee(1, '1500')
        self.assertEqual(Payment.objects.get(status='Pending').amount, D('300'))

    def test_history_rows_are_immutable(self):
        row = FeeChange.objects.first()
        row.reason = 'tampered'
        with self.assertRaises(PermissionError):
            row.save()
        with self.assertRaises(PermissionError):
            row.delete()

    def test_history_ordering_newest_first(self):
        services.update_total_fee(1, '1100')
        services.update_total_fee(1, '1300')
        self.assertEqual([h['new_total'] for h in services.get_history(1)], [D('1300'), D('1100'), D('1000')])


class FeeViewTests(TestCase):
    def setUp(self):
        self.warden = User.objects.create_user('w', password='Warden-Pass-123', is_staff=True)
        self.student_ref = 1
        services.create_fee_record(self.student_ref, '1000', '600')
        self.url = f'/warden/fees/{self.student_ref}/'
        self.client.force_login(self.warden)

    def test_list_and_detail_render(self):
        self.assertContains(self.client.get('/warden/fees/'), 'Student #1')
        r = self.client.get(self.url)
        self.assertContains(r, '1000')
        self.assertContains(r, 'Excess paid')

    def test_update_via_ui(self):
        self.client.post(self.url, {'total_fee': '1100', 'reason': ''})
        self.assertEqual(services.get_ledger(self.student_ref)['total_fee'], D('1100'))

    def test_lowering_without_reason_via_ui_shows_error(self):
        r = self.client.post(self.url, {'total_fee': '100', 'reason': ''})
        self.assertContains(r, 'reason is required')
        self.assertEqual(services.get_ledger(self.student_ref)['total_fee'], D('1000'))

    def test_missing_student_404(self):
        self.assertEqual(self.client.get('/warden/fees/9999/').status_code, 404)
