from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import Room, RoomAssignment, RoomRequest, RoomSwapNotification
from .student_service import StudentService


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
    """Return count of room requests awaiting warden action (ADR-005).

    Includes only CHANGE (PENDING) and SWAP (PENDING_WARDEN_APPROVAL);
    excludes PENDING_STUDENT_CONSENT.
    """
    return Room.get_pending_request_count()


OPEN_REQUEST_STATUSES = [
    RoomRequest.STATUS_PENDING,
    RoomRequest.STATUS_PENDING_STUDENT_CONSENT,
    RoomRequest.STATUS_PENDING_WARDEN_APPROVAL,
]


def get_available_rooms():
    """Return rooms with available_slots > 0 without any occupant PII (BR-08)."""
    rooms = Room.objects.all().order_by('room_number')
    available = []
    for room in rooms:
        slots = room.available_slots
        if slots > 0:
            available.append({
                'id': room.id,
                'room_number': room.room_number,
                'capacity': room.capacity,
                'available_slots': slots,
            })
    return available


def _has_open_request(student_id):
    return RoomRequest.objects.filter(
        student_id=student_id,
        status__in=OPEN_REQUEST_STATUSES,
    ).exists()


def submit_change_request(student_id, preferred_room_id, reason):
    """Submit a room-change request for an active student (FR-10, BR-07)."""
    sid = str(student_id or '').strip()
    clean_reason = str(reason or '').strip()
    if not clean_reason:
        raise ValueError("Reason is required.")

    student_info = StudentService.validate_active_student(sid)
    if not student_info:
        raise ValueError("Active student record not found.")

    if _has_open_request(sid):
        raise ValueError("You already have an open room request.")

    room = Room.objects.filter(pk=preferred_room_id).first()
    if not room:
        raise ValueError("Preferred room not found.")
    if room.available_slots <= 0:
        raise ValueError(f"Room {room.room_number} is full.")

    return RoomRequest.objects.create(
        student_id=sid,
        request_type=RoomRequest.TYPE_CHANGE,
        preferred_room=room,
        reason=clean_reason,
        status=RoomRequest.STATUS_PENDING,
    )


def submit_swap_request(student_id, target_student_id, reason):
    """Submit a two-step room-swap request requiring target student consent (OQ-04)."""
    sid = str(student_id or '').strip()
    target_sid = str(target_student_id or '').strip()
    clean_reason = str(reason or '').strip()

    if not clean_reason:
        raise ValueError("Reason is required.")
    if not target_sid:
        raise ValueError("Target student ID is required.")
    if sid == target_sid:
        raise ValueError("You cannot request a room swap with yourself.")

    if _has_open_request(sid):
        raise ValueError("You already have an open room request.")

    requester_info = StudentService.validate_active_student(sid)
    if not requester_info or requester_info.get('user_id') is None:
        raise ValueError("Active requester student record not found.")

    target_info = StudentService.validate_active_student(target_sid)
    if not target_info or target_info.get('user_id') is None:
        raise ValueError(f"Target student '{target_sid}' was not found or is not Active.")

    req_assign = RoomAssignment.objects.filter(
        student_id=str(requester_info['user_id']),
        is_active=True,
    ).first()
    if not req_assign:
        raise ValueError("You must have an active room assignment to request a swap.")

    target_assign = RoomAssignment.objects.filter(
        student_id=str(target_info['user_id']),
        is_active=True,
    ).first()
    if not target_assign:
        raise ValueError(f"Target student '{target_sid}' does not have an active room assignment.")

    if req_assign.room_id == target_assign.room_id:
        raise ValueError("You and the target student are already assigned to the same room.")

    req = RoomRequest.objects.create(
        student_id=sid,
        request_type=RoomRequest.TYPE_SWAP,
        target_student_id=target_sid,
        reason=clean_reason,
        status=RoomRequest.STATUS_PENDING_STUDENT_CONSENT,
    )
    RoomSwapNotification.objects.create(
        recipient_student_id=target_sid,
        room_request=req,
        notification_type=RoomSwapNotification.TYPE_SWAP_INCOMING,
        message=f"Student {sid} has requested a room swap with you.",
    )
    return req


@transaction.atomic
def respond_to_swap(request_id, student_id, accept: bool):
    """Allow target student to accept or decline an incoming swap request (OQ-04)."""
    sid = str(student_id or '').strip()
    req = RoomRequest.objects.select_for_update().filter(pk=request_id).first()
    if not req:
        raise ValueError("Room request not found.")
    if req.request_type != RoomRequest.TYPE_SWAP:
        raise ValueError("Only swap requests require student consent.")
    if req.target_student_id != sid:
        raise PermissionError("You are not authorized to respond to this swap request.")
    if req.status != RoomRequest.STATUS_PENDING_STUDENT_CONSENT:
        raise ValueError("This swap request is no longer awaiting your consent.")

    req.decided_by_student_at = timezone.now()
    if accept:
        req.status = RoomRequest.STATUS_PENDING_WARDEN_APPROVAL
        req.save(update_fields=['status', 'decided_by_student_at', 'updated_at'])
        RoomSwapNotification.objects.create(
            recipient_student_id=req.student_id,
            room_request=req,
            notification_type=RoomSwapNotification.TYPE_SWAP_ACCEPTED_BY_TARGET,
            message=f"Student {sid} accepted your room swap request. It is now pending warden approval.",
        )
    else:
        req.status = RoomRequest.STATUS_REJECTED_BY_STUDENT
        req.save(update_fields=['status', 'decided_by_student_at', 'updated_at'])
        RoomSwapNotification.objects.create(
            recipient_student_id=req.student_id,
            room_request=req,
            notification_type=RoomSwapNotification.TYPE_SWAP_REJECTED_BY_TARGET,
            message=f"Student {sid} declined your room swap request.",
        )
    return req


@transaction.atomic
def cancel_request(request_id, student_id):
    """Cancel an open room request by its requester without deleting the record (BR-05, BR-07)."""
    sid = str(student_id or '').strip()
    req = RoomRequest.objects.select_for_update().filter(pk=request_id).first()
    if not req:
        raise ValueError("Room request not found.")
    if req.student_id != sid:
        raise PermissionError("You can only cancel your own room requests.")
    if req.status not in OPEN_REQUEST_STATUSES:
        raise ValueError("Only open room requests can be cancelled.")

    req.status = RoomRequest.STATUS_CANCELLED
    req.save(update_fields=['status', 'updated_at'])
    return req


@transaction.atomic
def decide_change_request(request_id, approve: bool, remark=None):
    """Warden approves or rejects a Pending room-change request (FR-11, EC-41, EC-44)."""
    req = RoomRequest.objects.select_for_update().filter(pk=request_id).first()
    if not req:
        raise ValueError("Room request not found.")
    if req.request_type != RoomRequest.TYPE_CHANGE:
        raise ValueError("Request is not a room-change request.")
    if req.status == RoomRequest.STATUS_CANCELLED:
        raise ValueError("Cannot decide a request that was cancelled by the student.")
    if req.status != RoomRequest.STATUS_PENDING:
        raise ValueError("Only Pending room-change requests can be decided.")

    req.decided_by_warden_at = timezone.now()
    req.warden_remark = str(remark or '').strip()

    if not approve:
        req.status = RoomRequest.STATUS_REJECTED
        req.save(update_fields=['status', 'warden_remark', 'decided_by_warden_at', 'updated_at'])
        return req

    room = Room.objects.select_for_update().filter(pk=req.preferred_room_id).first()
    if not room:
        raise ValueError("Preferred room no longer exists.")
    if room.is_full:
        raise ValueError(f"Room {room.room_number} is now full.")

    student_info = StudentService.validate_active_student(req.student_id)
    if not student_info or student_info.get('user_id') is None:
        raise ValueError("Requester is no longer an active student.")

    assign_student_to_room(room.id, student_info['user_id'])
    req.status = RoomRequest.STATUS_APPROVED
    req.save(update_fields=['status', 'warden_remark', 'decided_by_warden_at', 'updated_at'])
    return req


@transaction.atomic
def decide_swap(request_id, approve: bool, remark=None):
    """Warden approves or rejects a swap request in PENDING_WARDEN_APPROVAL (OQ-05, EC-43, EC-44)."""
    req = RoomRequest.objects.select_for_update().filter(pk=request_id).first()
    if not req:
        raise ValueError("Room request not found.")
    if req.request_type != RoomRequest.TYPE_SWAP:
        raise ValueError("Request is not a room-swap request.")
    if req.status == RoomRequest.STATUS_CANCELLED:
        raise ValueError("Cannot decide a request that was cancelled by the student.")
    if req.status != RoomRequest.STATUS_PENDING_WARDEN_APPROVAL:
        raise ValueError("Only swap requests awaiting warden approval can be decided.")

    req.decided_by_warden_at = timezone.now()
    req.warden_remark = str(remark or '').strip()

    if not approve:
        req.status = RoomRequest.STATUS_REJECTED
        req.save(update_fields=['status', 'warden_remark', 'decided_by_warden_at', 'updated_at'])
        for recipient in (req.student_id, req.target_student_id):
            RoomSwapNotification.objects.create(
                recipient_student_id=recipient,
                room_request=req,
                notification_type=RoomSwapNotification.TYPE_SWAP_REJECTED_BY_WARDEN,
                message="Your room swap request was rejected by the warden.",
            )
        return req

    requester_info = StudentService.validate_active_student(req.student_id)
    target_info = StudentService.validate_active_student(req.target_student_id)
    if (
        not requester_info
        or requester_info.get('user_id') is None
        or not target_info
        or target_info.get('user_id') is None
    ):
        raise ValueError("Both students must remain Active to complete a room swap.")

    req_user_id_str = str(requester_info['user_id'])
    target_user_id_str = str(target_info['user_id'])

    req_assign = RoomAssignment.objects.select_for_update().filter(
        student_id=req_user_id_str,
        is_active=True,
    ).select_related('room').first()
    target_assign = RoomAssignment.objects.select_for_update().filter(
        student_id=target_user_id_str,
        is_active=True,
    ).select_related('room').first()

    if not req_assign or not target_assign:
        raise ValueError("Both students must have active room assignments to complete the swap.")
    if req_assign.room_id == target_assign.room_id:
        raise ValueError("Both students are already assigned to the same room.")

    req_room = req_assign.room
    target_room = target_assign.room

    req_assign.is_active = False
    req_assign.save(update_fields=['is_active'])
    target_assign.is_active = False
    target_assign.save(update_fields=['is_active'])

    RoomAssignment.objects.create(room=target_room, student_id=req_user_id_str, is_active=True)
    RoomAssignment.objects.create(room=req_room, student_id=target_user_id_str, is_active=True)

    req.status = RoomRequest.STATUS_APPROVED
    req.save(update_fields=['status', 'warden_remark', 'decided_by_warden_at', 'updated_at'])

    RoomSwapNotification.objects.create(
        recipient_student_id=req.student_id,
        room_request=req,
        notification_type=RoomSwapNotification.TYPE_SWAP_APPROVED,
        message=f"Your room swap with {req.target_student_id} was approved. You are now assigned to Room {target_room.room_number}.",
    )
    RoomSwapNotification.objects.create(
        recipient_student_id=req.target_student_id,
        room_request=req,
        notification_type=RoomSwapNotification.TYPE_SWAP_APPROVED,
        message=f"Your room swap with {req.student_id} was approved. You are now assigned to Room {req_room.room_number}.",
    )
    return req
