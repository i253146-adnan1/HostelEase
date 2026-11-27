from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from dashboard.services import get_warden_pending_summary

from .guards import login_required_guard, student_required, warden_required
from .models import StudentProfile
from .services import remove_user_avatar, update_user_avatar

User = get_user_model()


def _get_own_student_profile(user):
    """Return the StudentProfile belonging to the given user, or fallback to hostel.Student."""
    profile = StudentProfile.objects.filter(user=user).first()
    if profile is not None:
        return profile
    try:
        from hostel import room_service, student_service
        from hostel.models import Student

        student = Student.objects.filter(user_id=user.pk).first()
        if student is None:
            student = student_service.get_student_by_id(getattr(user, 'student_id', None) or user.username)
        if student is None:
            return None
        room = room_service.get_student_room(student.student_id)
        return {
            'full_name': student.full_name,
            'student_id': student.student_id,
            'contact_number': student.contact_number,
            'guardian_name': student.guardian_name,
            'guardian_contact': student.guardian_contact_number,
            'room_number': room['room_number'] if room else '',
            'status': student.status,
            'is_active': student.status == Student.STATUS_ACTIVE,
        }
    except ImportError:
        return None


def _get_student_home_summary(user):
    """Aggregate consolidated own-record summary for VS-20 student home (read-only via services)."""
    summary = {
        'ledger': None,
        'pending_proofs': 0,
        'open_complaints': 0,
        'open_leave_status': None,
        'active_optouts': 0,
        'pending_room_requests': 0,
    }
    student_id = getattr(user, 'student_id', None) or user.username

    try:
        from hostel import student_service
        from hostel.models import RoomRequest, Student
        from finance import services as finance_services

        student = Student.objects.filter(user_id=user.pk).first() or student_service.get_student_by_id(student_id)
        if student is not None:
            summary['ledger'] = finance_services.get_ledger(student.pk)
            payments = finance_services.list_student_payments(student.pk)
            summary['pending_proofs'] = sum(1 for p in payments if p.status == 'Pending')
        summary['pending_room_requests'] = RoomRequest.objects.filter(
            student_id=student_id,
            status__in=['PENDING_WARDEN', 'AWAITING_PEER'],
        ).count()
    except ImportError:
        pass

    try:
        from operations import leave_service, meal_service
        from operations.complaint_service import ComplaintService

        complaints = ComplaintService.get_student_complaints(user)
        summary['open_complaints'] = sum(1 for c in complaints if c.status in ('Submitted', 'In Progress'))

        leaves = leave_service.list_student_leave_requests(student_id)
        open_leave = next((l for l in leaves if l.status in ('PENDING', 'APPROVED')), None)
        summary['open_leave_status'] = open_leave.get_status_display() if open_leave else None

        opt_outs = meal_service.list_student_opt_outs(student_id)
        summary['active_optouts'] = sum(1 for o in opt_outs if o.status == 'Active')
    except ImportError:
        pass

    return summary


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
            if (
                user.must_change_password
                and user.password_reset_expires_at is not None
                and timezone.now() > user.password_reset_expires_at
            ):
                messages.error(
                    request,
                    'Your temporary reset password has expired. Please contact the Main Warden to generate a new reset.',
                )
                return render(request, 'accounts/login.html', {'username': username})

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
        summary = get_warden_pending_summary()
        return render(
            request,
            'accounts/warden_dashboard.html',
            {'pending_summary': summary},
        )
    if request.user.role == 'student':
        profile = _get_own_student_profile(request.user)
        home_summary = _get_student_home_summary(request.user)
        return render(
            request,
            'accounts/student_dashboard.html',
            {'profile': profile, 'home_summary': home_summary},
        )
    return HttpResponseForbidden('Invalid user role.')


@student_required
def student_dashboard(request):
    """Render the student dashboard scoped strictly to the logged-in student."""
    profile = _get_own_student_profile(request.user)
    home_summary = _get_student_home_summary(request.user)
    return render(
        request,
        'accounts/student_dashboard.html',
        {'profile': profile, 'home_summary': home_summary},
    )


@student_required
def student_profile(request):
    """Render the read-only student profile scoped strictly to the logged-in student."""
    profile = _get_own_student_profile(request.user)
    return render(request, 'accounts/student_profile.html', {'profile': profile})


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
        request.user.password_reset_expires_at = None
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Your password has been updated successfully.')
        return redirect('accounts:dashboard')

    return render(request, 'accounts/change_password.html')


@login_required_guard
def avatar_settings_view(request):
    """Render the Profile / Display Picture settings page for the logged-in user."""
    return render(request, 'accounts/avatar_settings.html')


@login_required_guard
@require_POST
def avatar_upload_view(request):
    """Upload or replace the logged-in user's own display picture."""
    try:
        update_user_avatar(request.user, request.FILES.get('avatar'))
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
        return render(request, 'accounts/avatar_settings.html')

    messages.success(request, 'Display picture updated successfully.')
    return redirect('accounts:avatar_settings')


@login_required_guard
@require_POST
def avatar_remove_view(request):
    """Remove the logged-in user's own display picture."""
    if remove_user_avatar(request.user):
        messages.success(request, 'Display picture removed.')
    else:
        messages.info(request, 'No display picture to remove.')
    return redirect('accounts:avatar_settings')


def forgot_password_view(request):
    """Self-service password reset restricted exclusively to the Main Warden."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        form_data = {
            'username': username,
            'email': email,
            'mobile_number': mobile_number,
        }

        user = User.objects.filter(username=username).first()
        if user is None:
            messages.error(request, 'No matching Main Warden account was found.')
            return render(request, 'accounts/forgot_password.html', {'form_data': form_data})

        if not user.is_main_warden:
            if user.role == 'warden':
                messages.error(
                    request,
                    'Sub-wardens cannot use self-service Forgot Password. Please contact the Main Warden to reset your password.',
                )
            else:
                messages.error(
                    request,
                    'Students cannot use self-service Forgot Password. Please contact the Warden to reset your password.',
                )
            return render(request, 'accounts/forgot_password.html', {'form_data': form_data}, status=403)

        if (
            not email
            or not mobile_number
            or user.email.strip().lower() != email.lower()
            or user.mobile_number.strip() != mobile_number
        ):
            messages.error(request, 'Email or mobile number does not match the registered Main Warden details.')
            return render(request, 'accounts/forgot_password.html', {'form_data': form_data})

        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return render(request, 'accounts/forgot_password.html', {'form_data': form_data})

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'accounts/forgot_password.html', {'form_data': form_data})

        user.set_password(new_password)
        user.must_change_password = False
        user.password_reset_expires_at = None
        user.save()
        messages.success(request, 'Main Warden password reset successfully. You can now sign in.')
        return redirect('accounts:login')

    return render(request, 'accounts/forgot_password.html', {'form_data': {}})


@warden_required
def warden_list_view(request):
    """List all warden accounts so Main Warden can manage sub-warden password resets."""
    wardens = User.objects.filter(role='warden').order_by('-is_main_warden', 'username')
    return render(
        request,
        'accounts/warden_list.html',
        {'wardens': wardens},
    )


@warden_required
def warden_create_view(request):
    """Register a new sub-warden without logging out or switching the current warden's session."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()
        raw_password = request.POST.get('temporary_password', '').strip()
        form_data = request.POST

        if not full_name or not username or not email or not mobile_number:
            messages.error(request, 'Name, Warden ID/Username, Email, and Mobile Number are required.')
            return render(request, 'accounts/warden_create.html', {'form_data': form_data})

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Warden ID / Username "{username}" is already taken.')
            return render(request, 'accounts/warden_create.html', {'form_data': form_data})

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, f'Email "{email}" is already registered.')
            return render(request, 'accounts/warden_create.html', {'form_data': form_data})

        if User.objects.filter(mobile_number=mobile_number).exists():
            messages.error(request, f'Mobile number "{mobile_number}" is already registered.')
            return render(request, 'accounts/warden_create.html', {'form_data': form_data})

        temp_password = raw_password or get_random_string(10)
        if len(temp_password) < 8:
            messages.error(request, 'Initial password must be at least 8 characters long.')
            return render(request, 'accounts/warden_create.html', {'form_data': form_data})

        new_warden = User.objects.create_user(
            username=username,
            password=temp_password,
            role='warden',
            full_name=full_name,
            first_name=full_name[:150],
            email=email,
            mobile_number=mobile_number,
            is_main_warden=False,
            is_staff=True,
            is_superuser=False,
            must_change_password=True,
        )
        return render(
            request,
            'accounts/warden_create_success.html',
            {
                'created_warden': new_warden,
                'temporary_password': temp_password,
            },
        )

    return render(request, 'accounts/warden_create.html', {'form_data': {}})


@warden_required
def warden_reset_password_view(request, pk):
    """Allow only the Main Warden to reset a sub-warden's password with an expiring temp password."""
    if not getattr(request.user, 'is_main_warden', False):
        return HttpResponseForbidden('Only the Main Warden can reset sub-warden passwords.')

    target_warden = get_object_or_404(User, pk=pk, role='warden')
    if target_warden.is_main_warden:
        messages.error(request, 'Main Warden password cannot be reset via sub-warden reset.')
        return redirect('accounts:warden_list')

    if request.method == 'POST':
        main_warden_password = request.POST.get('main_warden_password', '')
        raw_temp_password = request.POST.get('temporary_password', '').strip()

        if not request.user.check_password(main_warden_password):
            messages.error(request, 'Your Main Warden password is incorrect.')
            return render(request, 'accounts/warden_reset_password.html', {'target_warden': target_warden})

        temp_password = raw_temp_password or get_random_string(10)
        if len(temp_password) < 8:
            messages.error(request, 'Temporary password must be at least 8 characters long.')
            return render(request, 'accounts/warden_reset_password.html', {'target_warden': target_warden})

        expires_at = timezone.now() + timedelta(hours=24)
        target_warden.set_password(temp_password)
        target_warden.must_change_password = True
        target_warden.password_reset_expires_at = expires_at
        target_warden.save()

        return render(
            request,
            'accounts/warden_reset_success.html',
            {
                'target_warden': target_warden,
                'temporary_password': temp_password,
                'expires_at': expires_at,
            },
        )

    return render(request, 'accounts/warden_reset_password.html', {'target_warden': target_warden})


@warden_required
def warden_profile_view(request):
    """Allow any logged-in warden to view and update their own Name, Email, and Mobile Number."""
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile_number = request.POST.get('mobile_number', '').strip()

        if not full_name or not email or not mobile_number:
            messages.error(request, 'Name, Email, and Mobile Number are required.')
            return render(request, 'accounts/warden_profile.html')

        if User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
            messages.error(request, f'Email "{email}" is already used by another account.')
            return render(request, 'accounts/warden_profile.html')

        if User.objects.filter(mobile_number=mobile_number).exclude(pk=request.user.pk).exists():
            messages.error(request, f'Mobile number "{mobile_number}" is already used by another account.')
            return render(request, 'accounts/warden_profile.html')

        request.user.full_name = full_name
        request.user.first_name = full_name[:150]
        request.user.email = email
        request.user.mobile_number = mobile_number
        request.user.save()
        messages.success(request, 'Your warden profile has been updated.')
        return redirect('accounts:warden_profile')

    return render(request, 'accounts/warden_profile.html')
