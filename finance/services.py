"""Fee & Payments service interface (VS-04).

Other modules call these functions; they never query finance tables directly.
``student_ref`` is the Student Management primary key (no cross-module FK).

Invariants (NFR-02, BR-10):
    paid_amount      = sum of Verified payments
    remaining_amount = max(total_fee - paid_amount, 0)
    excess_paid      = max(paid_amount - total_fee, 0)
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from operations import file_storage
from operations.models import StoredFile

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


def parse_payment_date(value):
    """Parse a payment date (date object or YYYY-MM-DD string) or raise FeeError."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or '').strip()
    if not text:
        raise FeeError('Payment date is required.')
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise FeeError('Payment date must be a valid date (YYYY-MM-DD).')


@transaction.atomic
def submit_payment_proof(*, student_ref, owner_user_id, amount, payment_date, proof_file):
    """Submit a student payment proof (VS-09, FR-04, AC-04.1, AC-04.2).

    Validates amount, date, and file (JPG/PNG/PDF <= 5 MB via VS-08) and saves
    the Payment as Pending without modifying verified paid totals.
    """
    value = parse_money(amount, 'Payment amount')
    if value <= 0:
        raise FeeError('Payment amount must be greater than zero.')
    parsed_date = parse_payment_date(payment_date)
    if proof_file is None:
        raise FeeError('Payment proof file is required.')

    try:
        stored = file_storage.save_uploaded_file(
            proof_file,
            category=StoredFile.CATEGORY_PAYMENT_PROOF,
            owner_user_id=owner_user_id,
            record_ref=f'student-{student_ref}',
        )
    except file_storage.FileStorageError as exc:
        raise FeeError(str(exc))

    return Payment.objects.create(
        student_ref=student_ref,
        amount=value,
        payment_date=parsed_date,
        status=Payment.STATUS_PENDING,
        source=Payment.SOURCE_PROOF,
        proof_file_key=stored.file_key,
        proof_file_name=stored.original_name,
    )


def list_student_payments(student_ref):
    return list(Payment.objects.filter(student_ref=student_ref))


def list_pending_payments():
    return list(Payment.objects.filter(status=Payment.STATUS_PENDING).order_by('-created_at', '-id'))


def count_pending_payments():
    return Payment.objects.filter(status=Payment.STATUS_PENDING).count()


def get_payment(payment_id):
    """Retrieve a Payment by primary key, or None."""
    return Payment.objects.filter(pk=payment_id).first()


@transaction.atomic
def verify_payment(payment_id, warden_username=''):
    """Verify a pending payment proof (VS-12, FR-06, BR-03, AC-05.1).

    Atomically changes status to Verified, records decision timestamp and warden username,
    and updates verified paid total, remaining, and excess paid consistently.
    Raises FeeError if the payment does not exist or has already been reviewed.
    """
    payment = Payment.objects.select_for_update().filter(pk=payment_id).first()
    if payment is None:
        raise FeeError('Payment record not found.')
    if payment.status != Payment.STATUS_PENDING:
        raise FeeError(f'Payment #{payment_id} has already been reviewed (current status: {payment.status}).')

    payment.status = Payment.STATUS_VERIFIED
    payment.decided_at = timezone.now()
    payment.decided_by = str(warden_username or '').strip()
    payment.save(update_fields=['status', 'decided_at', 'decided_by'])

    record = FeeRecord.objects.select_for_update().filter(student_ref=payment.student_ref).first()
    payment.ledger = _ledger(record) if record else None
    return payment


@transaction.atomic
def reject_payment(payment_id, remark, warden_username=''):
    """Reject a pending payment proof (VS-12, FR-06, BR-03, AC-05.2).

    Requires a non-empty remark. Atomically changes status to Rejected,
    records remark, timestamp, and warden username.
    Verified paid total, remaining, and excess paid remain unchanged.
    Raises FeeError if the payment does not exist, remark is missing,
    or the payment has already been reviewed.
    """
    clean_remark = str(remark or '').strip()
    if not clean_remark:
        raise FeeError('A rejection remark is required.')

    payment = Payment.objects.select_for_update().filter(pk=payment_id).first()
    if payment is None:
        raise FeeError('Payment record not found.')
    if payment.status != Payment.STATUS_PENDING:
        raise FeeError(f'Payment #{payment_id} has already been reviewed (current status: {payment.status}).')

    payment.status = Payment.STATUS_REJECTED
    payment.warden_remark = clean_remark
    payment.decided_at = timezone.now()
    payment.decided_by = str(warden_username or '').strip()
    payment.save(update_fields=['status', 'warden_remark', 'decided_at', 'decided_by'])

    record = FeeRecord.objects.select_for_update().filter(student_ref=payment.student_ref).first()
    payment.ledger = _ledger(record) if record else None
    return payment

