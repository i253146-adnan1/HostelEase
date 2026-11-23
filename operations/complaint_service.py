from django.core.exceptions import PermissionDenied
from django.db import transaction

from .models import Complaint


class ComplaintError(Exception):
    """Domain error for invalid complaint operations or transitions."""


class ComplaintService:
    """Service layer for student complaint submission and warden management (VS-10, VS-13)."""

    ALLOWED_TRANSITIONS = {
        'Submitted': ['In Progress'],
        'In Progress': ['Resolved'],
        'Resolved': [],
    }
    VALID_STATUSES = ('Submitted', 'In Progress', 'Resolved')

    @staticmethod
    def submit_complaint(student_user, category, description, stored_file=None):
        """Create and return a Complaint with status='Submitted'."""
        return Complaint.objects.create(
            student_user=student_user,
            category=category,
            description=description,
            attachment=stored_file,
            status='Submitted',
        )

    @staticmethod
    def get_student_complaints(student_user):
        """Return all complaints owned by student_user."""
        return Complaint.objects.filter(student_user=student_user).select_related('attachment')

    @staticmethod
    def get_complaint_detail(complaint_id, student_user):
        """Return a complaint by ID if owned by student_user; otherwise raise PermissionDenied."""
        complaint = Complaint.objects.select_related('attachment').get(pk=complaint_id)
        if complaint.student_user_id != student_user.pk:
            raise PermissionDenied('You do not have permission to view this complaint.')
        return complaint

    @classmethod
    def list_all_complaints(cls, status_filter=None):
        """Return all complaints for the warden, optionally filtered by status (FR-08)."""
        qs = Complaint.objects.select_related('student_user', 'attachment').all()
        if status_filter in cls.VALID_STATUSES:
            qs = qs.filter(status=status_filter)
        return qs

    @staticmethod
    def get_warden_complaint_detail(complaint_id):
        """Return any complaint by ID for warden management (FR-08)."""
        return Complaint.objects.select_related('student_user', 'attachment').get(pk=complaint_id)

    @classmethod
    @transaction.atomic
    def update_complaint_status(cls, complaint_id, new_status, remark=''):
        """Transition a complaint's status along Submitted -> In Progress -> Resolved (FR-08, BR-04, OQ-03, OQ-12)."""
        try:
            complaint = Complaint.objects.select_for_update().get(pk=complaint_id)
        except Complaint.DoesNotExist as exc:
            raise ComplaintError('Complaint not found.') from exc

        allowed = cls.ALLOWED_TRANSITIONS.get(complaint.status, [])
        if new_status not in allowed:
            raise ComplaintError(
                f'Cannot transition complaint from "{complaint.status}" to "{new_status}".'
            )

        cleaned_remark = (remark or '').strip()
        if new_status == 'Resolved' and not cleaned_remark:
            raise ComplaintError('A remark is required when marking a complaint as Resolved.')

        complaint.status = new_status
        if cleaned_remark:
            complaint.warden_remark = cleaned_remark
        complaint.save(update_fields=['status', 'warden_remark', 'updated_at'])
        return complaint

    @staticmethod
    def get_pending_count():
        """Return count of Submitted + In Progress complaints for Dashboard (ADR-005)."""
        return Complaint.objects.filter(
            status__in=['Submitted', 'In Progress']
        ).count()
