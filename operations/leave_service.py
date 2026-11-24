"""Leave Requests service layer (VS-15, FR-17, BR-05, BR-12, OQ-30, ADR-005).

Module Boundary:
- Owns LeaveRequest records in the `operations` app.
- Validates student existence and Active status via `hostel.student_service.StudentService.validate_active_student`
  instead of querying `Student` directly.
- Exposes `get_pending_count()` as the read-only interface for the future Dashboard (ADR-005).
- Never deletes LeaveRequest records (BR-05).
"""
from django.db import transaction
from django.utils import timezone

from hostel.student_service import StudentService

from .models import LeaveRequest


def _normalize_decision(warden_decision):
    """Return True for approve, False for reject, or raise ValueError."""
    if isinstance(warden_decision, bool):
        return warden_decision
    normalized = str(warden_decision or '').strip().upper()
    if normalized in ('APPROVE', 'APPROVED'):
        return True
    if normalized in ('REJECT', 'REJECTED'):
        return False
    raise ValueError('Invalid warden decision. Expected APPROVE or REJECT.')


@transaction.atomic
def submit_leave_request(student_id, departure_date, return_date, reason):
    """Validate and create a new LeaveRequest with status=PENDING (AC-17.1, EC-47, EC-48, OQ-30)."""
    student_info = StudentService.validate_active_student(student_id)
    if not student_info:
        raise ValueError('Only an existing Active student can submit a leave request.')
    canonical_student_id = student_info['student_id']

    if not departure_date or not return_date:
        raise ValueError('Both departure date and return date are required.')

    # EC-47 / AC-17.2: return_date must be strictly after departure_date.
    if return_date <= departure_date:
        raise ValueError('Return date must be strictly after the departure date.')

    reason_text = str(reason or '').strip()
    if not reason_text:
        raise ValueError('Reason for leave is required.')

    # EC-48 / AC-17.3 / OQ-30 (Log 27): one open (PENDING or APPROVED) leave request per student.
    has_open_request = LeaveRequest.objects.filter(
        student_id=canonical_student_id,
        status__in=[LeaveRequest.STATUS_PENDING, LeaveRequest.STATUS_APPROVED],
    ).exists()
    if has_open_request:
        raise ValueError(
            'You already have an open (Pending or Approved) leave request. '
            'Only one open leave request is allowed at a time.'
        )

    return LeaveRequest.objects.create(
        student_id=canonical_student_id,
        departure_date=departure_date,
        return_date=return_date,
        reason=reason_text,
        status=LeaveRequest.STATUS_PENDING,
    )


@transaction.atomic
def decide_leave_request(request_id, warden_decision, remark=None):
    """Approve or reject a PENDING LeaveRequest (FR-17, AC-17.4, BR-12).

    BR-12 / AC-17.4 CONSTRAINT:
    This function MUST NOT touch Student.status, RoomAssignment, or the
    auth/session layer in any way — it only updates the LeaveRequest row.
    """
    approve = _normalize_decision(warden_decision)
    leave_req = LeaveRequest.objects.select_for_update().filter(pk=request_id).first()
    if not leave_req:
        raise ValueError('Leave request not found.')

    if leave_req.status != LeaveRequest.STATUS_PENDING:
        raise ValueError('Only pending leave requests can be decided.')

    remark_text = str(remark or '').strip()
    now = timezone.now()

    if approve:
        leave_req.status = LeaveRequest.STATUS_APPROVED
        leave_req.warden_remark = remark_text or None
    else:
        if not remark_text:
            raise ValueError('A remark is required when rejecting a leave request.')
        leave_req.status = LeaveRequest.STATUS_REJECTED
        leave_req.warden_remark = remark_text

    leave_req.decided_by_warden_at = now
    leave_req.save(update_fields=['status', 'warden_remark', 'decided_by_warden_at', 'updated_at'])
    return leave_req


def get_pending_count():
    """Return count of LeaveRequest rows with status=PENDING for Dashboard (ADR-005)."""
    return LeaveRequest.objects.filter(status=LeaveRequest.STATUS_PENDING).count()


def list_student_leave_requests(student_id):
    """Return all leave requests owned by `student_id`, newest first."""
    sid = str(student_id or '').strip()
    if not sid:
        return LeaveRequest.objects.none()
    return LeaveRequest.objects.filter(student_id=sid)


def list_pending_leave_requests():
    """Return all PENDING leave requests for the warden review queue."""
    return LeaveRequest.objects.filter(status=LeaveRequest.STATUS_PENDING)


def list_decided_leave_requests():
    """Return recent APPROVED/REJECTED leave requests for warden reference."""
    return LeaveRequest.objects.filter(
        status__in=[LeaveRequest.STATUS_APPROVED, LeaveRequest.STATUS_REJECTED]
    )


class LeaveService:
    """Service facade for Leave Requests module (architecture.md / ADR-005)."""

    @staticmethod
    def submit_leave_request(student_id, departure_date, return_date, reason):
        return submit_leave_request(student_id, departure_date, return_date, reason)

    @staticmethod
    def decide_leave_request(request_id, warden_decision, remark=None):
        return decide_leave_request(request_id, warden_decision, remark=remark)

    @staticmethod
    def get_pending_count():
        return get_pending_count()
