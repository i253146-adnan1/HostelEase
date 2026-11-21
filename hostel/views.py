from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from . import services
from .forms import RoomForm
from .models import Room, RoomAssignment


def _warden_required(view_func):
    """Manual staff/warden check matching ADR-003 Auth Guard pattern."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('/accounts/login/')
        return view_func(request, *args, **kwargs)
    return _wrapped


@_warden_required
@require_GET
def room_list(request):
    rooms = Room.objects.all().order_by('room_number')
    return render(request, 'hostel/room_list.html', {'rooms': rooms})


@_warden_required
@require_GET
def room_detail(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    active_assignments = room.assignments.filter(is_active=True).select_related('student_user')
    return render(
        request,
        'hostel/room_detail.html',
        {'room': room, 'active_assignments': active_assignments},
    )


@_warden_required
def room_create(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"Room {room.room_number} created.")
            return redirect('hostel:room_list')
    else:
        form = RoomForm()
    return render(request, 'hostel/room_form.html', {'form': form, 'is_edit': False})


@_warden_required
def room_edit(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"Room {room.room_number} updated.")
            return redirect('hostel:room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'hostel/room_form.html', {'form': form, 'room': room, 'is_edit': True})


@_warden_required
@require_POST
def room_delete(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if not services.can_remove_room(room.pk):
        messages.error(request, f"Cannot remove room {room.room_number}: students are currently assigned.")
        return redirect('hostel:room_detail', room_id=room.pk)

    try:
        room_number = room.room_number
        room.delete()
        messages.success(request, f"Room {room_number} removed.")
        return redirect('hostel:room_list')
    except ProtectedError:
        messages.error(request, f"Cannot remove room {room.room_number}: historical assignments exist.")
        return redirect('hostel:room_detail', room_id=room.pk)


@_warden_required
@require_POST
def room_assign(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    raw_user_id = request.POST.get('user_id', '').strip()
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        messages.error(request, "Please provide a valid numeric user ID.")
        return redirect('hostel:room_detail', room_id=room.pk)

    User = get_user_model()
    try:
        services.assign_student_to_room(room.pk, user_id)
        messages.success(request, f"Student assigned to room {room.room_number}.")
    except ValueError as exc:
        messages.error(request, str(exc))
    except User.DoesNotExist:
        messages.error(request, f"User with ID {user_id} does not exist.")

    return redirect('hostel:room_detail', room_id=room.pk)


@_warden_required
@require_POST
def room_clear_assignment(request, assignment_id):
    assignment = get_object_or_404(RoomAssignment, pk=assignment_id)
    if assignment.student_user_id is not None:
        cleared = services.clear_student_room_assignment(assignment.student_user_id)
        if cleared:
            messages.success(request, "Student room assignment cleared.")
        else:
            messages.info(request, "Assignment was already inactive.")
    else:
        assignment.is_active = False
        assignment.save(update_fields=['is_active'])
        messages.success(request, "Room assignment cleared.")

    return redirect('hostel:room_detail', room_id=assignment.room_id)
