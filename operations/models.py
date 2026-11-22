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
