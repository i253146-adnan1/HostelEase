from django.conf import settings
from django.db import models


class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number}"

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
        """Placeholder service interface for VS-11 (Dashboard reads this)."""
        return 0


class RoomAssignment(models.Model):
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='assignments')
    # TODO: Replace with ForeignKey to Student model after VS-02 is complete
    student_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='room_assignment',
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student_user} -> {self.room} ({'active' if self.is_active else 'inactive'})"
