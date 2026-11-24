"""Read-only Dashboard aggregation service (VS-19, FR-14, ADR-005).

Dashboard owns NO database tables and never queries module tables directly.
It aggregates pending-item counts strictly through each module's public
service interface:
    - Fee & Payments: finance.services.count_pending_payments()
    - Complaints:     operations.complaint_service.ComplaintService.get_pending_count()
    - Rooms:          hostel.services.get_pending_request_count()
    - Leave Requests: LeaveService.get_pending_count() (when VS-15 is present)

Per ADR-005, Meal Opt-Outs are intentionally excluded from the pending-items
dashboard.
"""
from importlib import import_module

from finance import services as finance_services
from hostel import services as hostel_services
from operations.complaint_service import ComplaintService


def _resolve_leave_pending_count():
    """Read pending leave request count via Leave Requests service interface.

    VS-15 (Leave Requests) is a separate vertical slice. When its service
    module is present, delegate to its ``get_pending_count()`` interface;
    until VS-15 is merged, report 0 with ``available=False``.
    """
    candidates = (
        ('operations.leave_service', 'LeaveService', 'get_pending_count'),
        ('leave.services', None, 'get_pending_count'),
        ('hostel.leave_service', None, 'get_pending_count'),
    )
    for module_path, class_name, method_name in candidates:
        try:
            mod = import_module(module_path)
        except ModuleNotFoundError:
            continue
        target = getattr(mod, class_name, None) if class_name else mod
        fn = getattr(target, method_name, None) if target is not None else None
        if callable(fn):
            return int(fn()), True
    return 0, False


def get_warden_pending_summary(leave_count_provider=None):
    """Return read-only pending-item counts for the warden dashboard (FR-14, ADR-005)."""
    pending_payment_proofs = int(finance_services.count_pending_payments())
    pending_complaints = int(ComplaintService.get_pending_count())
    pending_room_requests = int(hostel_services.get_pending_request_count())

    if leave_count_provider is not None:
        pending_leave_requests = int(leave_count_provider())
        leave_module_available = True
    else:
        pending_leave_requests, leave_module_available = _resolve_leave_pending_count()

    total_pending = (
        pending_payment_proofs
        + pending_complaints
        + pending_room_requests
        + pending_leave_requests
    )

    return {
        'pending_payment_proofs': pending_payment_proofs,
        'pending_complaints': pending_complaints,
        'pending_room_requests': pending_room_requests,
        'pending_leave_requests': pending_leave_requests,
        'total_pending': total_pending,
        'leave_module_available': leave_module_available,
    }
