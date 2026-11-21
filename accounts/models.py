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

    def __str__(self):
        return f'{self.username} ({self.role})'
