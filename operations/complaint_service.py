from django.core.exceptions import PermissionDenied

from .models import Complaint


class ComplaintService:
    """Service layer for student complaint submission and read queries (VS-10)."""

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

    @staticmethod
    def get_pending_count():
        """Return count of Submitted + In Progress complaints for Dashboard (ADR-005)."""
        return Complaint.objects.filter(
            status__in=['Submitted', 'In Progress']
        ).count()
