import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Feedback(models.Model):
    """Feedback entity (FR-15, BR-11, BR-05).

    Students submit 1-5 star ratings for:
    - Food
    - Rooms
    - Washrooms
    - Environment

    Invariants:
    - BR-11: Submitted feedback cannot be edited.
    - BR-05: Feedback records are never hard-deleted.
    - Module Boundary: References student_id as logical string; no cross-module FK.
    """

    student_id = models.CharField(max_length=50, db_index=True)
    food_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    room_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    washroom_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    environment_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError('Submitted feedback cannot be edited.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('Feedback records cannot be deleted.')

    def __str__(self):
        return f'Feedback #{self.pk} by {self.student_id} on {self.created_at:%Y-%m-%d}'


class StoredFile(models.Model):
    """Database path reference & metadata for locally stored uploads (VS-08, ADR-004)."""

    CATEGORY_PAYMENT_PROOF = 'payment_proof'
    CATEGORY_COMPLAINT_ATTACHMENT = 'complaint_attachment'
    CATEGORY_CHOICES = [
        (CATEGORY_PAYMENT_PROOF, 'Payment Proof'),
        (CATEGORY_COMPLAINT_ATTACHMENT, 'Complaint Attachment'),
    ]

    file_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    owner_user_id = models.PositiveIntegerField(db_index=True)
    record_ref = models.CharField(max_length=64, blank=True)
    original_name = models.CharField(max_length=255)
    relative_path = models.CharField(max_length=500, unique=True)
    content_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def delete(self, *args, **kwargs):
        raise PermissionError('Stored file records cannot be hard-deleted.')

    def __str__(self):
        return f'{self.category}:{self.file_key} ({self.original_name})'


class Complaint(models.Model):
    """Student complaint entity (FR-07, AC-07.1-AC-07.4, BR-05)."""

    CATEGORY_CHOICES = [
        ('room_furniture', 'Room and Furniture'),
        ('electricity_water', 'Electricity and Water'),
        ('cleanliness_hygiene', 'Cleanliness and Hygiene'),
        ('food_mess', 'Food and Mess'),
        ('internet', 'Internet'),
        ('security_safety', 'Security and Safety'),
        ('behavior_conduct', 'Behavior or Conduct of Other Residents'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    student_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='complaints',
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField()
    attachment = models.ForeignKey(
        StoredFile,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='complaint_attachments',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    warden_remark = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def delete(self, *args, **kwargs):
        raise PermissionError('Complaint records cannot be hard-deleted (BR-05).')

    def __str__(self):
        return f'{self.get_category_display()} — {self.student_user.username} — {self.status}'

