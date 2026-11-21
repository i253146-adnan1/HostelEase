from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .guards import login_required_guard


def login_view(request):
    """Authenticate a user and start a server-side session."""
    if request.user.is_authenticated:
        if getattr(request.user, 'must_change_password', False):
            return redirect('accounts:change_password')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.must_change_password:
                return redirect('accounts:change_password')

            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('accounts:dashboard')

        messages.error(request, 'Invalid username or password.')
        return render(request, 'accounts/login.html', {'username': username})

    return render(request, 'accounts/login.html')


@require_POST
def logout_view(request):
    """Log out the current user via POST and redirect to home."""
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required_guard
def dashboard_view(request):
    """Route authenticated users to their role-specific dashboard."""
    if request.user.role == 'warden':
        return render(request, 'accounts/warden_dashboard.html')
    if request.user.role == 'student':
        return render(request, 'accounts/student_dashboard.html')
    return HttpResponseForbidden('Invalid user role.')


@login_required_guard
def change_password_view(request):
    """Allow an authenticated user to change their password."""
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'accounts/change_password.html')

        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return render(request, 'accounts/change_password.html')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'accounts/change_password.html')

        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Your password has been updated successfully.')
        return redirect('accounts:dashboard')

    return render(request, 'accounts/change_password.html')
