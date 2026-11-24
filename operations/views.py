from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST

from accounts.guards import login_required_guard, student_required, warden_required
from hostel.student_service import StudentService
from . import feedback_service, file_storage, leave_service
from .complaint_form import ComplaintForm
from .complaint_service import ComplaintService
from .feedback_service import FeedbackError
from .models import Complaint, LeaveRequest, StoredFile


@student_required
def student_feedback_view(request):
    """Allow logged-in student to submit 1-5 star ratings for hostel aspects (FR-15, AC-15.1)."""
    # Use student_id attribute or username as student identifier
    student_id = getattr(request.user, 'student_id', None) or request.user.username
    past_submissions = feedback_service.list_student_feedback(student_id)

    if request.method == 'POST':
        food = request.POST.get('food_rating')
        room = request.POST.get('room_rating')
        washroom = request.POST.get('washroom_rating')
        environment = request.POST.get('environment_rating')

        try:
            feedback_service.submit_feedback(
                student_id=student_id,
                food=food,
                room=room,
                washroom=washroom,
                environment=environment,
            )
            messages.success(request, 'Thank you! Your feedback has been recorded successfully.')
            return redirect('operations:student_feedback')
        except FeedbackError as exc:
            messages.error(request, str(exc))
            return render(request, 'operations/student_feedback.html', {
                'past_submissions': past_submissions,
                'form_data': request.POST,
            })

    return render(request, 'operations/student_feedback.html', {
        'past_submissions': past_submissions,
        'form_data': {},
    })


@warden_required
def warden_feedback_summary_view(request):
    """Allow warden to view aggregated rating distribution per star level and aspect (FR-15, AC-15.4)."""
    summary = feedback_service.get_feedback_summary()
    return render(request, 'operations/warden_feedback_summary.html', {
        'summary': summary,
        'star_range': [5, 4, 3, 2, 1],  # Highest to lowest for chart display
    })


@login_required_guard
def download_stored_file(request, file_key):
    """Serve a stored file only to its owner student or the warden (VS-08, NFR-01)."""
    stored_file = file_storage.get_stored_file(file_key)
    if stored_file is None:
        raise Http404('File not found.')
    if not file_storage.can_access_file(request.user, stored_file):
        return HttpResponseForbidden('You do not have permission to access this file.')
    try:
        handle = file_storage.open_stored_file(stored_file)
    except FileNotFoundError:
        raise Http404('File not found on disk.')
    response = FileResponse(handle, content_type=stored_file.content_type or 'application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{stored_file.original_name}"'
    return response


@student_required
def student_complaint_list(request):
    """List complaints submitted by the logged-in student (FR-07, AC-07.4)."""
    complaints = ComplaintService.get_student_complaints(request.user)
    return render(request, 'operations/complaint_list.html', {
        'complaints': complaints,
    })


@student_required
def student_complaint_submit(request):
    """Allow logged-in student to submit a complaint with optional attachment (FR-07, AC-07.1-AC-07.3)."""
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data.get('attachment')
            stored_file = None
            if uploaded:
                stored_file = file_storage.save_uploaded_file(
                    uploaded,
                    category=StoredFile.CATEGORY_COMPLAINT_ATTACHMENT,
                    owner_user_id=request.user.pk,
                    record_ref='',
                )
            complaint = ComplaintService.submit_complaint(
                request.user,
                form.cleaned_data['category'],
                form.cleaned_data['description'],
                stored_file,
            )
            if stored_file is not None:
                stored_file.record_ref = str(complaint.pk)
                stored_file.save(update_fields=['record_ref'])
            messages.success(request, 'Your complaint has been submitted successfully.')
            return redirect('operations:complaint_list')
    else:
        form = ComplaintForm()

    return render(request, 'operations/complaint_submit.html', {
        'form': form,
    })


@student_required
def student_complaint_detail(request, complaint_id):
    """Show complaint details to its owning student only (AC-07.4, NFR-01)."""
    try:
        complaint = ComplaintService.get_complaint_detail(complaint_id, request.user)
    except PermissionDenied:
        return HttpResponseForbidden('You do not have permission to view this complaint.')
    except Complaint.DoesNotExist:
        raise Http404('Complaint not found.')

    return render(request, 'operations/complaint_detail.html', {
        'complaint': complaint,
    })


def _get_active_student_id(request):
    """Resolve logged-in user to an Active Student.student_id via StudentService (VS-15)."""
    candidate_id = getattr(request.user, 'student_id', None) or request.user.username
    info = StudentService.validate_active_student(candidate_id)
    if not info:
        return None
    return info['student_id']


@student_required
@require_GET
def student_leave_requests(request):
    """List only the logged-in student's own leave requests (FR-17, NFR-01)."""
    sid = _get_active_student_id(request)
    if not sid:
        return HttpResponseForbidden('Active student record required.')

    my_requests = leave_service.list_student_leave_requests(sid)
    return render(request, 'operations/student_leave_requests.html', {
        'requests': my_requests,
    })


@student_required
def student_leave_request_create(request):
    """Submit a temporary leave request for the logged-in active student (FR-17, AC-17.1-17.3)."""
    sid = _get_active_student_id(request)
    if not sid:
        return HttpResponseForbidden('Active student record required.')

    if request.method == 'POST':
        raw_departure = request.POST.get('departure_date', '').strip()
        raw_return = request.POST.get('return_date', '').strip()
        reason = request.POST.get('reason', '')

        departure_date = parse_date(raw_departure) if raw_departure else None
        return_date = parse_date(raw_return) if raw_return else None

        try:
            if not departure_date or not return_date:
                raise ValueError('Please enter valid departure and return dates.')
            leave_service.submit_leave_request(sid, departure_date, return_date, reason)
            messages.success(request, 'Leave request submitted and is now Pending.')
            return redirect('operations:student_leave_requests')
        except ValueError as exc:
            messages.error(request, str(exc))

    return render(request, 'operations/student_leave_request_form.html', {
        'form_data': request.POST if request.method == 'POST' else {},
    })


@warden_required
@require_GET
def warden_leave_requests(request):
    """Warden queue of PENDING leave requests and recent decisions (FR-17, AC-17.4)."""
    pending_requests = leave_service.list_pending_leave_requests()
    recent_history = leave_service.list_decided_leave_requests()[:20]
    return render(request, 'operations/warden_leave_requests.html', {
        'pending_requests': pending_requests,
        'recent_history': recent_history,
        'pending_count': leave_service.get_pending_count(),
    })


@warden_required
@require_POST
def warden_decide_leave_request(request, request_id):
    """Warden approves or rejects a PENDING leave request (FR-17, AC-17.4, BR-12)."""
    leave_req = get_object_or_404(LeaveRequest, pk=request_id)
    action = request.POST.get('action', '').strip().lower()
    remark = request.POST.get('remark', '')

    if action not in ('approve', 'reject'):
        messages.error(request, 'Invalid decision action.')
        return redirect('operations:warden_leave_requests')

    decision = 'APPROVE' if action == 'approve' else 'REJECT'
    try:
        leave_service.decide_leave_request(leave_req.pk, decision, remark=remark)
        messages.success(
            request,
            f'Leave request #{leave_req.pk} {"approved" if action == "approve" else "rejected"}.',
        )
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect('operations:warden_leave_requests')

