from django.core.exceptions import ValidationError
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
