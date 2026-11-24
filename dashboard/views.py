from django.shortcuts import render

from accounts.guards import warden_required

from .services import get_warden_pending_summary


@warden_required
def warden_dashboard_view(request):
    """Render the warden pending-items dashboard (VS-19, FR-14, AC-14.1, AC-14.2)."""
    summary = get_warden_pending_summary()
    return render(
        request,
        'accounts/warden_dashboard.html',
        {'pending_summary': summary},
    )
