from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.urls import reverse


def _must_change_password_redirect(request):
    """Redirect authenticated users with must_change_password=True to change-password."""
    if not request.user.is_authenticated or not getattr(request.user, 'must_change_password', False):
        return None

    change_password_url = reverse('accounts:change_password')
    logout_url = reverse('accounts:logout')
    if request.path in (change_password_url, logout_url):
        return None

    static_url = getattr(settings, 'STATIC_URL', None)
    media_url = getattr(settings, 'MEDIA_URL', None)
    if static_url and request.path.startswith(f'/{static_url.lstrip("/")}'):
        return None
    if media_url and request.path.startswith(f'/{media_url.lstrip("/")}'):
        return None

    messages.warning(request, 'You must change your password before continuing.')
    return redirect('accounts:change_password')


class ForcePasswordChangeMiddleware:
    """Enforce password change across all routes when must_change_password is True."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        redirect_response = _must_change_password_redirect(request)
        if redirect_response is not None:
            return redirect_response
        return self.get_response(request)


def login_required_guard(view_func):
    """Redirect anonymous users to LOGIN_URL and enforce forced password change."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        redirect_response = _must_change_password_redirect(request)
        if redirect_response is not None:
            return redirect_response
        return view_func(request, *args, **kwargs)

    return _wrapped


def _role_required(required_role, forbidden_message):
    def decorator(view_func):
        @login_required_guard
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if getattr(request.user, 'role', None) != required_role:
                return render(request, '403.html', {'message': forbidden_message}, status=403)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


warden_required = _role_required('warden', 'Access denied. Warden role required.')
student_required = _role_required('student', 'Access denied. Student role required.')
