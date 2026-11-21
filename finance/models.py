from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class FeeRecord(models.Model):
    """Fee & Payments module: one fee record per student (student_ref = Student pk)."""

    student_ref = models.PositiveIntegerField(unique=True)
    total_fee = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)


class FeeChange(models.Model):
    """Immutable audit row for every total-fee change (old, new, date, reason)."""

    fee_record = models.ForeignKey(FeeRecord, on_delete=models.PROTECT, related_name='changes')
    old_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_total = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    changed_by = models.CharField(max_length=150, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at', '-id']

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError('Fee-change history is immutable.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('Fee-change history is immutable.')


class Payment(models.Model):
    """Minimal payment ledger entry. Only Verified rows count towards paid_amount.

    Proof upload / verification workflows belong to later slices (VS-09, VS-12);
    this table exists so the ledger aggregation (VS-04) and opening balance
    (OQ-26) have a defined source. No payment gateway (C-01).
    """

    STATUS_PENDING = 'Pending'
    STATUS_VERIFIED = 'Verified'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    SOURCE_OPENING = 'opening_balance'
    SOURCE_PROOF = 'proof'

    student_ref = models.PositiveIntegerField(db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    source = models.CharField(max_length=20, default=SOURCE_PROOF)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
