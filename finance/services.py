"""Fee & Payments service interface (VS-04).

Other modules call these functions; they never query finance tables directly.
``student_ref`` is the Student Management primary key (no cross-module FK).

Invariants (NFR-02, BR-10):
    paid_amount      = sum of Verified payments
    remaining_amount = max(total_fee - paid_amount, 0)
    excess_paid      = max(paid_amount - total_fee, 0)
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum

from .models import FeeChange, FeeRecord, Payment

ZERO = Decimal('0.00')
MAX_AMOUNT = Decimal('99999999.99')


class FeeError(Exception):
    """Business-rule violation in the Fee & Payments module."""


def parse_money(value, label='Amount'):
    """Return a non-negative Decimal with 2 decimal places or raise FeeError."""
    if isinstance(value, Decimal):
        amount = value
    else:
        text = str(value if value is not None else '').strip()
        if not text:
            raise FeeError(f'{label} is required.')
        try:
            amount = Decimal(text)
        except InvalidOperation:
            raise FeeError(f'{label} must be a number.')
    if not amount.is_finite():
        raise FeeError(f'{label} must be a number.')
    if amount < 0:
        raise FeeError(f'{label} cannot be negative.')
    if amount > MAX_AMOUNT:
        raise FeeError(f'{label} is too large.')
    if amount != amount.quantize(Decimal('0.01')):
        raise FeeError(f'{label} can have at most 2 decimal places.')
    return amount.quantize(Decimal('0.01'))


def _paid(student_ref):
    total = Payment.objects.filter(
        student_ref=student_ref, status=Payment.STATUS_VERIFIED
    ).aggregate(s=Sum('amount'))['s']
    return total or ZERO


def _ledger(record):
    paid = _paid(record.student_ref)
    total = record.total_fee
    return {
        'student_ref': record.student_ref,
        'total_fee': total,
        'paid_amount': paid,
        'remaining_amount': max(total - paid, ZERO),
        'excess_paid': max(paid - total, ZERO),
    }


@transaction.atomic
def create_fee_record(student_ref, total_fee, opening_paid=0, changed_by=''):
    """Create the initial fee record, history row and optional opening balance (OQ-26)."""
    total = parse_money(total_fee, 'Total fee')
    opening = parse_money(opening_paid if opening_paid not in (None, '') else 0, 'Opening paid amount')
    if FeeRecord.objects.filter(student_ref=student_ref).exists():
        raise FeeError('A fee record already exists for this student.')
    record = FeeRecord.objects.create(student_ref=student_ref, total_fee=total)
    FeeChange.objects.create(
        fee_record=record, old_total=None, new_total=total,
        reason='Initial fee set at registration', changed_by=changed_by,
    )
    if opening > 0:
        Payment.objects.create(
            student_ref=student_ref, amount=opening, status=Payment.STATUS_VERIFIED,
            source=Payment.SOURCE_OPENING, note='Opening balance entered at registration',
        )
    return _ledger(record)


def get_ledger(student_ref):
    """Return the ledger dict, or None when the student has no fee record."""
    record = FeeRecord.objects.filter(student_ref=student_ref).first()
    return _ledger(record) if record else None


def list_ledgers():
    return [_ledger(r) for r in FeeRecord.objects.all().order_by('student_ref')]


@transaction.atomic
def update_total_fee(student_ref, new_total, reason='', changed_by=''):
    """Change the total fee and append an immutable history row.

    Lowering the total below the verified paid amount requires a reason.
    Payment rows are never touched.
    """
    new_total = parse_money(new_total, 'Total fee')
    reason = (reason or '').strip()
    record = FeeRecord.objects.select_for_update().filter(student_ref=student_ref).first()
    if record is None:
        raise FeeError('No fee record exists for this student.')
    if new_total == record.total_fee:
        raise FeeError('The new total fee is the same as the current total fee.')
    if new_total < _paid(student_ref) and not reason:
        raise FeeError(
            'A reason is required when the total fee is lowered below the amount already paid.'
        )
    FeeChange.objects.create(
        fee_record=record, old_total=record.total_fee, new_total=new_total,
        reason=reason, changed_by=changed_by,
    )
    record.total_fee = new_total
    record.save(update_fields=['total_fee'])
    return _ledger(record)


def get_history(student_ref):
    return list(
        FeeChange.objects.filter(fee_record__student_ref=student_ref).values(
            'old_total', 'new_total', 'reason', 'changed_by', 'changed_at'
        )
    )


def add_payment(student_ref, amount, status=Payment.STATUS_PENDING, source=Payment.SOURCE_PROOF):
    """Interface for the later proof workflow (VS-09/VS-12). Only Verified counts as paid."""
    if status not in dict(Payment.STATUS_CHOICES):
        raise FeeError('Invalid payment status.')
    value = parse_money(amount, 'Payment amount')
    if value <= 0:
        raise FeeError('Payment amount must be greater than zero.')
    Payment.objects.create(student_ref=student_ref, amount=value, status=status, source=source)
