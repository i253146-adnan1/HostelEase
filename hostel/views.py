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
    active_assignments = room.assignments.filter(is_active=True)
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
    if assignment.student_id is not None:
        cleared = services.clear_student_room_assignment(assignment.student_id)
        if cleared:
            messages.success(request, "Student room assignment cleared.")
        else:
            messages.info(request, "Assignment was already inactive.")
    else:
        assignment.is_active = False
        assignment.save(update_fields=['is_active'])
        messages.success(request, "Room assignment cleared.")

    return redirect('hostel:room_detail', room_id=assignment.room_id)

from django.http import HttpResponseForbidden
from . import student_service
from .models import Student
from finance import services as finance_services


def _warden_portal_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')
        if getattr(request.user, 'role', None) != 'warden' and not request.user.is_staff:
            return HttpResponseForbidden('Forbidden')
        return view_func(request, *args, **kwargs)
    return _wrapped


@_warden_portal_required
def warden_student_list(request):
    students = student_service.list_students()
    records = []
    for s in students:
        assign = RoomAssignment.objects.filter(student_id=s.student_id, is_active=True).select_related('room').first()
        ledger = finance_services.get_ledger(s.id)
        records.append({
            'student': s,
            'room': assign.room if assign else None,
            'ledger': ledger,
        })
    return render(request, 'hostel/warden_student_list.html', {'records': records})


@_warden_portal_required
def warden_student_create(request):
    rooms = Room.objects.all().order_by('room_number')
    if request.method == 'POST':
        try:
            result = student_service.register_student(
                full_name=request.POST.get('full_name', ''),
                student_id=request.POST.get('student_id', ''),
                contact_number=request.POST.get('contact_number', ''),
                guardian_name=request.POST.get('guardian_name', ''),
                guardian_contact_number=request.POST.get('guardian_contact_number', ''),
                room_identifier=request.POST.get('room', ''),
                total_fee=request.POST.get('total_fee', ''),
                opening_paid=request.POST.get('opening_paid', '0'),
                email=request.POST.get('email', ''),
                address=request.POST.get('address', ''),
                temporary_password=request.POST.get('temporary_password', ''),
                created_by=request.user.username,
            )
            return render(request, 'hostel/warden_student_success.html', result)
        except student_service.StudentError as exc:
            messages.error(request, str(exc))
            return render(request, 'hostel/warden_student_create.html', {
                'rooms': rooms,
                'error': str(exc),
                'form_data': request.POST,
            })
    return render(request, 'hostel/warden_student_create.html', {'rooms': rooms, 'form_data': {}})


@_warden_portal_required
def warden_student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    assign = RoomAssignment.objects.filter(student_id=student.student_id, is_active=True).select_related('room').first()
    ledger = finance_services.get_ledger(student.id)
    fee_history = finance_services.get_history(student.id)
    return render(request, 'hostel/warden_student_detail.html', {
        'student': student,
        'room': assign.room if assign else None,
        'ledger': ledger,
        'fee_history': fee_history,
    })


# --- Hostel Information (VS-06: Announcements, Mess Menu, Rules) ---

from django import forms as django_forms
from .models import Announcement, MenuItem, Rule


def _clean_non_empty(value, field_label):
    if not value or not value.strip():
        raise django_forms.ValidationError(f'{field_label} cannot be empty.')
    return value.strip()


class AnnouncementForm(django_forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'message']
        widgets = {
            'title': django_forms.TextInput(attrs={'class': 'form-control'}),
            'message': django_forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_title(self):
        return _clean_non_empty(self.cleaned_data.get('title'), 'Title')

    def clean_message(self):
        return _clean_non_empty(self.cleaned_data.get('message'), 'Message')


class MenuItemForm(django_forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['day_of_week', 'meal_type', 'items']
        widgets = {
            'day_of_week': django_forms.Select(attrs={'class': 'form-select'}),
            'meal_type': django_forms.Select(attrs={'class': 'form-select'}),
            'items': django_forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_items(self):
        return _clean_non_empty(self.cleaned_data.get('items'), 'Menu items')


class RuleForm(django_forms.ModelForm):
    class Meta:
        model = Rule
        fields = ['title', 'description']
        widgets = {
            'title': django_forms.TextInput(attrs={'class': 'form-control'}),
            'description': django_forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_title(self):
        return _clean_non_empty(self.cleaned_data.get('title'), 'Title')

    def clean_description(self):
        return _clean_non_empty(self.cleaned_data.get('description'), 'Description')


def _handle_info_form(request, form_class, template_name, redirect_name, success_msg, page_title, cancel_url_name, instance=None):
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, success_msg)
            return redirect(redirect_name)
    else:
        form = form_class(instance=instance)

    return render(request, template_name, {
        'form': form,
        'page_title': page_title,
        'cancel_url_name': cancel_url_name,
        'is_edit': instance is not None,
    })


def _handle_info_delete(request, model_class, pk, redirect_name, success_msg, item_type, cancel_url_name):
    obj = get_object_or_404(model_class, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, success_msg)
        return redirect(redirect_name)

    return render(request, 'hostel/confirm_delete.html', {
        'object': obj,
        'item_type': item_type,
        'cancel_url_name': cancel_url_name,
    })


def student_announcements(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    return render(request, 'hostel/student_announcements.html', {
        'announcements': Announcement.objects.all(),
    })


def student_menu(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    return render(request, 'hostel/student_menu.html', {
        'menu_items': MenuItem.objects.all(),
    })


def student_rules(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    return render(request, 'hostel/student_rules.html', {
        'rules': Rule.objects.all(),
    })


@_warden_portal_required
def warden_announcements(request):
    return render(request, 'hostel/warden_announcements.html', {
        'announcements': Announcement.objects.all(),
    })


@_warden_portal_required
def announcement_create(request):
    return _handle_info_form(
        request, AnnouncementForm, 'hostel/entry_form.html',
        'hostel:warden_announcements', 'Announcement published.',
        'Publish Announcement', 'hostel:warden_announcements',
    )


@_warden_portal_required
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    return _handle_info_form(
        request, AnnouncementForm, 'hostel/entry_form.html',
        'hostel:warden_announcements', 'Announcement updated.',
        'Edit Announcement', 'hostel:warden_announcements', instance=announcement,
    )


@_warden_portal_required
def announcement_delete(request, pk):
    return _handle_info_delete(
        request, Announcement, pk, 'hostel:warden_announcements',
        'Announcement removed.', 'Announcement', 'hostel:warden_announcements',
    )


@_warden_portal_required
def warden_menu(request):
    return render(request, 'hostel/warden_menu.html', {
        'menu_items': MenuItem.objects.all(),
    })


@_warden_portal_required
def menu_create(request):
    return _handle_info_form(
        request, MenuItemForm, 'hostel/entry_form.html',
        'hostel:warden_menu', 'Menu entry added.',
        'Add Menu Entry', 'hostel:warden_menu',
    )


@_warden_portal_required
def menu_edit(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    return _handle_info_form(
        request, MenuItemForm, 'hostel/entry_form.html',
        'hostel:warden_menu', 'Menu entry updated.',
        'Edit Menu Entry', 'hostel:warden_menu', instance=menu_item,
    )


@_warden_portal_required
def menu_delete(request, pk):
    return _handle_info_delete(
        request, MenuItem, pk, 'hostel:warden_menu',
        'Menu entry removed.', 'Menu Entry', 'hostel:warden_menu',
    )


@_warden_portal_required
def warden_rules(request):
    return render(request, 'hostel/warden_rules.html', {
        'rules': Rule.objects.all(),
    })


@_warden_portal_required
def rule_create(request):
    return _handle_info_form(
        request, RuleForm, 'hostel/entry_form.html',
        'hostel:warden_rules', 'Rule added.',
        'Add Rule', 'hostel:warden_rules',
    )


@_warden_portal_required
def rule_edit(request, pk):
    rule = get_object_or_404(Rule, pk=pk)
    return _handle_info_form(
        request, RuleForm, 'hostel/entry_form.html',
        'hostel:warden_rules', 'Rule updated.',
        'Edit Rule', 'hostel:warden_rules', instance=rule,
    )


@_warden_portal_required
def rule_delete(request, pk):
    return _handle_info_delete(
        request, Rule, pk, 'hostel:warden_rules',
        'Rule removed.', 'Rule', 'hostel:warden_rules',
    )
