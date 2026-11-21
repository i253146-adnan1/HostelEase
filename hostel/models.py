from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


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
        return 0

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

