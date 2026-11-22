from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import redirect, render

from accounts.guards import login_required_guard, student_required, warden_required
from . import feedback_service, file_storage
from .feedback_service import FeedbackError


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
