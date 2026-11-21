from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Room, RoomAssignment


@transaction.atomic
def assign_student_to_room(room_id, student_id):
    """
    Assigns student_user to room.
    Raises ValueError if room is full.
    Deactivates any existing active assignment for this student first.
    Creates new RoomAssignment.
    Returns the new RoomAssignment.
    """
    room = Room.objects.select_for_update().get(pk=room_id)
    if room.is_full:
        raise ValueError(f"Room {room.room_number} is full.")

    User = get_user_model()
    student_user = User.objects.get(pk=student_id)

    RoomAssignment.objects.filter(
        student_id=str(student_user.pk),
        is_active=True,
    ).update(is_active=False)

    return RoomAssignment.objects.create(
        room=room,
        student_id=str(student_user.pk),
        is_active=True,
    )


def clear_student_room_assignment(student_id):
    """
    Deactivates the student's current active RoomAssignment.
    Returns True if an assignment was cleared, False if none existed.
    """
    updated = RoomAssignment.objects.filter(
        student_id=str(student_id),
        is_active=True,
    ).update(is_active=False)
    return updated > 0


def get_room_occupancy(room_id):
    """Returns current active occupancy count for the room."""
    room = Room.objects.get(pk=room_id)
    return room.occupancy


def can_remove_room(room_id):
    """Returns True if room has zero active assignments."""
    return not RoomAssignment.objects.filter(room_id=room_id, is_active=True).exists()


def get_pending_request_count():
    """Placeholder. Returns 0. Will be implemented in VS-11."""
    return Room.get_pending_request_count()
