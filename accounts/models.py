from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for HostelEase supporting Warden and Student roles."""

    ROLE_CHOICES = [
        ('warden', 'Warden'),
        ('student', 'Student'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
    )
    must_change_password = models.BooleanField(default=False)
    student_id = models.CharField(max_length=50, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f'{self.username} ({self.role})'


class StudentProfile(models.Model):
    """Student profile storing personal, guardian, room, and status details."""

    STATUS_ACTIVE = 'Active'
    STATUS_LEFT = 'Left'
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Left', 'Left'),
    ]

    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    guardian_name = models.CharField(max_length=200)
    guardian_contact = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    room_number = models.CharField(max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.student_id})'

    def is_active(self):
        return self.status == self.STATUS_ACTIVE
