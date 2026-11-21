"""Rooms module service interface (VS-03 contract).

Other modules call these functions; they never query room tables directly.
``student_id`` is the Student identifier string (no cross-module FK).

Invariants (BR-06):
    - Room capacity must never be exceeded.
    - Full rooms reject new assignments.
    - Capacity cannot be reduced below current occupancy.
    - Occupancy reflects active room assignments.
"""
from django.db import transaction
from django.db.models import Count, Q

from .models import Room, RoomAssignment


class RoomError(Exception):
    """Business rule violation in Rooms module."""


class RoomNotFoundError(RoomError):
    """Requested room does not exist."""


class RoomFullError(RoomError):
    """Target room is at capacity and cannot accept new assignments."""


def _resolve_room(room_identifier, for_update=False):
    """Find a Room by ID or room_number."""
    qs = Room.objects.select_for_update() if for_update else Room.objects.all()

    if isinstance(room_identifier, Room):
        if for_update:
            return qs.filter(pk=room_identifier.pk).first()
        return room_identifier

    if isinstance(room_identifier, int) or (isinstance(room_identifier, str) and str(room_identifier).isdigit()):
        room = qs.filter(pk=int(room_identifier)).first()
        if room:
            return room

    room = qs.filter(room_number=str(room_identifier).strip()).first()
    if not room:
        raise RoomNotFoundError(f"Room '{room_identifier}' not found.")
    return room


def list_rooms():
    """Return catalogue of all rooms with capacity and active occupancy."""
    rooms = Room.objects.annotate(
        occupancy=Count('assignments', filter=Q(assignments__is_active=True))
    ).order_by('room_number')

    result = []
    for r in rooms:
        occupancy = getattr(r, 'occupancy', 0)
        result.append({
            'id': r.id,
            'room_number': r.room_number,
            'capacity': r.capacity,
            'occupancy': occupancy,
            'is_full': occupancy >= r.capacity,
            'available_spots': max(r.capacity - occupancy, 0),
        })
    return result


def get_room(room_identifier):
    """Retrieve room details by ID or room_number."""
    room = _resolve_room(room_identifier)
    occupancy = RoomAssignment.objects.filter(room=room, is_active=True).count()
    return {
        'id': room.id,
        'room_number': room.room_number,
        'capacity': room.capacity,
        'occupancy': occupancy,
        'is_full': occupancy >= room.capacity,
        'available_spots': max(room.capacity - occupancy, 0),
        'instance': room,
    }


def create_room(room_number, capacity):
    """Create a new room with capacity >= 1."""
    number = str(room_number or '').strip()
    if not number:
        raise RoomError('Room number is required.')
    try:
        cap = int(capacity)
        if cap < 1:
            raise ValueError()
    except (TypeError, ValueError):
        raise RoomError('Room capacity must be a positive integer.')

    if Room.objects.filter(room_number=number).exists():
        raise RoomError(f"Room '{number}' already exists.")

    return Room.objects.create(room_number=number, capacity=cap)


@transaction.atomic
def update_room(room_identifier, room_number=None, capacity=None):
    """Update room details. Capacity cannot be reduced below current occupancy."""
    room = _resolve_room(room_identifier, for_update=True)
    current_occupancy = RoomAssignment.objects.filter(room=room, is_active=True).count()

    if capacity is not None:
        try:
            new_cap = int(capacity)
            if new_cap < 1:
                raise ValueError()
        except (TypeError, ValueError):
            raise RoomError('Room capacity must be a positive integer.')

        if new_cap < current_occupancy:
            raise RoomError(
                f"Cannot reduce capacity to {new_cap}; current occupancy is {current_occupancy}."
            )
        room.capacity = new_cap

    if room_number is not None:
        new_number = str(room_number).strip()
        if not new_number:
            raise RoomError('Room number cannot be empty.')
        if Room.objects.filter(room_number=new_number).exclude(pk=room.pk).exists():
            raise RoomError(f"Room '{new_number}' already exists.")
        room.room_number = new_number

    room.save()
    return room


def get_occupancy(room_identifier):
    """Return active student count for a room."""
    room = _resolve_room(room_identifier)
    return RoomAssignment.objects.filter(room=room, is_active=True).count()


def get_student_room(student_id):
    """Return active room info for a student, or None."""
    sid = str(student_id or '').strip()
    assignment = RoomAssignment.objects.filter(
        student_id=sid, is_active=True
    ).select_related('room').first()
    if not assignment:
        return None
    return {
        'room_id': assignment.room.id,
        'room_number': assignment.room.room_number,
        'capacity': assignment.room.capacity,
        'assigned_at': assignment.assigned_at,
    }


@transaction.atomic
def assign_student(student_id, room_identifier):
    """Assign an existing student if capacity is available.

    Enforces BR-06: Room capacity must never be exceeded.
    """
    sid = str(student_id or '').strip()
    if not sid:
        raise RoomError('Student ID is required for room assignment.')

    room = _resolve_room(room_identifier, for_update=True)

    # Check current active occupancy
    active_assignments = RoomAssignment.objects.filter(room=room, is_active=True)
    current_occupancy = active_assignments.count()

    # Check if student already assigned to this room
    existing_in_room = active_assignments.filter(student_id=sid).first()
    if existing_in_room:
        return existing_in_room

    if current_occupancy >= room.capacity:
        raise RoomFullError(
            f"Room {room.room_number} is full. Capacity cannot be exceeded."
        )

    # Deactivate any previous room assignment for this student
    RoomAssignment.objects.filter(student_id=sid, is_active=True).update(is_active=False)

    return RoomAssignment.objects.create(
        room=room,
        student_id=sid,
        is_active=True,
    )


@transaction.atomic
def clear_student_room(student_id):
    """Clear active room assignment for student (used when student leaves, FR-13)."""
    sid = str(student_id or '').strip()
    return RoomAssignment.objects.filter(student_id=sid, is_active=True).update(is_active=False)
