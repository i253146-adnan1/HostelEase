from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.guards import warden_required

from .i18n import get_warden_dashboard_i18n, set_warden_dashboard_lang
from .services import get_warden_pending_summary


@warden_required
def warden_dashboard_view(request):
    """Render the warden pending-items dashboard (VS-19, VS-23)."""
    summary = get_warden_pending_summary()
    return render(
        request,
        'accounts/warden_dashboard.html',
        {
            'pending_summary': summary,
            'warden_i18n': get_warden_dashboard_i18n(request),
        },
    )


@warden_required
@require_POST
def set_warden_language_view(request):
    """Toggle Warden Dashboard UI language in the server-side session (VS-23)."""
    set_warden_dashboard_lang(request, request.POST.get('lang', 'en'))
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('dashboard:warden_dashboard')
