"""Visitor Log service layer (VS-17, FR-18, BR-13, BR-05, EC-49, OQ-32).

Warden-only business logic for recording visitor arrivals and check-outs.
Module boundary:
- Validates student_id existence via hostel.student_service.StudentService.student_exists()
  (never queries the Student table directly).
- No delete operation is exposed (conservative OQ-32 default under BR-05).
- No student-facing read/list interface is exposed (BR-13).
"""

from django.utils import timezone

from hostel.student_service import StudentService
from .models import VisitorLogEntry


class VisitorLogError(Exception):
    """Domain validation error for Visitor Log operations."""


def create_visitor_entry(visitor_name, student_id, purpose, check_in_time):
    """Create a visitor log entry after validating student existence (FR-18, AC-18.1, AC-18.2, EC-49)."""
    name = str(visitor_name or '').strip()
    sid = str(student_id or '').strip()
    visit_purpose = str(purpose or '').strip()

    if not name:
        raise VisitorLogError('Visitor name is required.')
    if not sid:
        raise VisitorLogError('Student ID is required.')
    if not visit_purpose:
        raise VisitorLogError('Purpose of visit is required.')
    if check_in_time is None:
        raise VisitorLogError('Check-in time is required.')

    if timezone.is_naive(check_in_time):
        check_in_time = timezone.make_aware(check_in_time, timezone.get_current_timezone())

    # Existence-only check per Log 28 (does not require Active status).
    if not StudentService.student_exists(sid):
        raise VisitorLogError(f'No student record found for student ID "{sid}".')

    return VisitorLogEntry.objects.create(
        visitor_name=name,
        student_id=sid,
        purpose=visit_purpose,
        check_in_time=check_in_time,
    )


def record_check_out(entry_id, check_out_time):
    """Record check-out time on a visitor entry that has not yet checked out (FR-18, AC-18.3).

    Rejects attempts to overwrite an existing check_out_time.
    """
    if check_out_time is None:
        raise VisitorLogError('Check-out time is required.')

    if timezone.is_naive(check_out_time):
        check_out_time = timezone.make_aware(check_out_time, timezone.get_current_timezone())

    entry = VisitorLogEntry.objects.filter(pk=entry_id).first()
    if entry is None:
        raise VisitorLogError('Visitor log entry not found.')

    if entry.check_out_time is not None:
        raise VisitorLogError('Check-out time has already been recorded for this visitor entry.')

    if check_out_time < entry.check_in_time:
        raise VisitorLogError('Check-out time cannot be earlier than check-in time.')

    entry.check_out_time = check_out_time
    entry.save(update_fields=['check_out_time', 'updated_at'])
    return entry


def list_visitor_entries():
    """Return all visitor log entries ordered newest-first (for warden views only; BR-13)."""
    return VisitorLogEntry.objects.all()
