from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Announcement(models.Model):
    """Hostel-wide announcement published by the warden."""

    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if not self.title or not self.title.strip():
            raise ValidationError({'title': 'Title cannot be empty.'})
        if not self.message or not self.message.strip():
            raise ValidationError({'message': 'Message cannot be empty.'})

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    """Hostel mess menu entry managed by the warden."""

    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    MEAL_CHOICES = [
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Snacks', 'Snacks'),
        ('Dinner', 'Dinner'),
    ]

    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    items = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def clean(self):
        if not self.items or not self.items.strip():
            raise ValidationError({'items': 'Menu items cannot be empty.'})

    def __str__(self):
        return f'{self.day_of_week} - {self.meal_type}'


class MessTiming(models.Model):
    """Editable hostel breakfast and dinner timings."""

    breakfast_timing = models.CharField(max_length=100, default='7:30 AM – 9:30 AM')
    dinner_timing = models.CharField(max_length=100, default='6:00 PM – 8:00 PM')
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_current(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'breakfast_timing': '7:30 AM – 9:30 AM',
                'dinner_timing': '6:00 PM – 8:00 PM',
            },
        )
        return obj

    def __str__(self):
        return f'Breakfast: {self.breakfast_timing} | Dinner: {self.dinner_timing}'


class Rule(models.Model):
    """Hostel rule published and maintained by the warden."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def clean(self):
        if not self.title or not self.title.strip():
            raise ValidationError({'title': 'Title cannot be empty.'})
        if not self.description or not self.description.strip():
            raise ValidationError({'description': 'Description cannot be empty.'})

    def __str__(self):
        return self.title


class Room(models.Model):
    """Room catalogue entity (VS-03). Owned by Rooms module."""

    room_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']


    @property
    def occupancy(self):
        return self.assignments.filter(is_active=True).count()

    @property
    def is_full(self):
        return self.occupancy >= self.capacity

    @property
    def available_slots(self):
        return self.capacity - self.occupancy

    @classmethod
    def get_pending_request_count(cls):
        return RoomRequest.objects.filter(
            Q(request_type=RoomRequest.TYPE_CHANGE, status=RoomRequest.STATUS_PENDING)
            | Q(request_type=RoomRequest.TYPE_SWAP, status=RoomRequest.STATUS_PENDING_WARDEN_APPROVAL)
        ).count()

    def __str__(self):
        return f'Room {self.room_number}'


class RoomAssignment(models.Model):
    """Active/historical room assignments for students. No cross-module FK to Student."""

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='assignments')
    student_id = models.CharField(max_length=50, db_index=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-assigned_at', '-id']

    def __str__(self):
        return f'{self.student_id} -> Room {self.room.room_number} (active={self.is_active})'


class Student(models.Model):
    """Student record managed by Warden (FR-01, BR-04, BR-05, BR-09, FR-13)."""

    STATUS_ACTIVE = 'Active'
    STATUS_LEFT = 'Left'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_LEFT, 'Left'),
    ]

    student_id = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20)
    guardian_name = models.CharField(max_length=150)
    guardian_contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    user_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f'{self.student_id} - {self.full_name}'


class RoomRequest(models.Model):
    """Student room-change or two-step room-swap request (VS-11, OQ-04/OQ-05)."""

    TYPE_CHANGE = 'CHANGE'
    TYPE_SWAP = 'SWAP'
    REQUEST_TYPE_CHOICES = [
        (TYPE_CHANGE, 'Room Change'),
        (TYPE_SWAP, 'Room Swap'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_PENDING_STUDENT_CONSENT = 'PENDING_STUDENT_CONSENT'
    STATUS_REJECTED_BY_STUDENT = 'REJECTED_BY_STUDENT'
    STATUS_PENDING_WARDEN_APPROVAL = 'PENDING_WARDEN_APPROVAL'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PENDING_STUDENT_CONSENT, 'Pending Student Consent'),
        (STATUS_REJECTED_BY_STUDENT, 'Rejected by Student'),
        (STATUS_PENDING_WARDEN_APPROVAL, 'Pending Warden Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    student_id = models.CharField(max_length=50, db_index=True)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    preferred_room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='change_requests',
    )
    target_student_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    reason = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, db_index=True)
    warden_remark = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    decided_by_student_at = models.DateTimeField(null=True, blank=True)
    decided_by_warden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'RoomRequest #{self.pk} ({self.request_type} by {self.student_id} - {self.status})'


class RoomSwapNotification(models.Model):
    """In-app notification for two-step room-swap workflow (VS-11)."""

    TYPE_SWAP_INCOMING = 'SWAP_INCOMING'
    TYPE_SWAP_ACCEPTED_BY_TARGET = 'SWAP_ACCEPTED_BY_TARGET'
    TYPE_SWAP_REJECTED_BY_TARGET = 'SWAP_REJECTED_BY_TARGET'
    TYPE_SWAP_APPROVED = 'SWAP_APPROVED'
    TYPE_SWAP_REJECTED_BY_WARDEN = 'SWAP_REJECTED_BY_WARDEN'
    NOTIFICATION_TYPE_CHOICES = [
        (TYPE_SWAP_INCOMING, 'Incoming Swap Request'),
        (TYPE_SWAP_ACCEPTED_BY_TARGET, 'Swap Accepted by Target'),
        (TYPE_SWAP_REJECTED_BY_TARGET, 'Swap Rejected by Target'),
        (TYPE_SWAP_APPROVED, 'Swap Approved'),
        (TYPE_SWAP_REJECTED_BY_WARDEN, 'Swap Rejected by Warden'),
    ]

    recipient_student_id = models.CharField(max_length=50, db_index=True)
    room_request = models.ForeignKey(
        RoomRequest,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.notification_type} for {self.recipient_student_id} (read={self.is_read})'


