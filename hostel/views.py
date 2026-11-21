from functools import wraps

from django import forms
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.guards import warden_required
from finance import services as finance_services
from . import room_service, student_service
from .models import Announcement, MenuItem, Rule, Room, RoomAssignment, Student
from .student_service import StudentError
from .room_service import RoomError


def _is_warden(user):
    """Return True if the authenticated user has warden privileges."""
    if not user or not user.is_authenticated:
        return False
    role = getattr(user, 'role', None)
    if role is not None:
        return str(role).lower() == 'warden'
    return user.is_staff or user.is_superuser


def _warden_required(view_func):
    """Deny access with 403 Forbidden if the user is not the warden."""
    # TODO: align with VS-01 Auth & Access Guard when available
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _is_warden(request.user):
            return HttpResponseForbidden('Only the warden can perform this action.')
        return view_func(request, *args, **kwargs)

    return _wrapped


def _clean_non_empty(value, field_label):
    if not value or not value.strip():
        raise forms.ValidationError(f'{field_label} cannot be empty.')
    return value.strip()


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_title(self):
        return _clean_non_empty(self.cleaned_data.get('title'), 'Title')

    def clean_message(self):
        return _clean_non_empty(self.cleaned_data.get('message'), 'Message')


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['day_of_week', 'meal_type', 'items']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'items': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_items(self):
        return _clean_non_empty(self.cleaned_data.get('items'), 'Menu items')


class RuleForm(forms.ModelForm):
    class Meta:
        model = Rule
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_title(self):
        return _clean_non_empty(self.cleaned_data.get('title'), 'Title')

    def clean_description(self):
        return _clean_non_empty(self.cleaned_data.get('description'), 'Description')


def _handle_form(request, form_class, template_name, redirect_name, success_msg, page_title, cancel_url_name, instance=None):
    """Shared create/edit form handler for hostel info entries."""
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


def _handle_delete(request, model_class, pk, redirect_name, success_msg, item_type, cancel_url_name):
    """Shared delete confirmation and removal handler for hostel info entries."""
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


# --- Student Read-Only Views ---

# TODO: add login_required after VS-01
def student_announcements(request):
    announcements = Announcement.objects.all()
    return render(request, 'hostel/student_announcements.html', {
        'announcements': announcements,
    })


# TODO: add login_required after VS-01
def student_menu(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'hostel/student_menu.html', {
        'menu_items': menu_items,
    })


# TODO: add login_required after VS-01
def student_rules(request):
    rules = Rule.objects.all()
    return render(request, 'hostel/student_rules.html', {
        'rules': rules,
    })


# --- Warden Management Views: Announcements ---

@_warden_required
def warden_announcements(request):
    announcements = Announcement.objects.all()
    return render(request, 'hostel/warden_announcements.html', {
        'announcements': announcements,
    })


@_warden_required
def announcement_create(request):
    return _handle_form(
        request,
        AnnouncementForm,
        'hostel/entry_form.html',
        'hostel:warden_announcements',
        'Announcement published.',
        'Publish Announcement',
        'hostel:warden_announcements',
    )


@_warden_required
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    return _handle_form(
        request,
        AnnouncementForm,
        'hostel/entry_form.html',
        'hostel:warden_announcements',
        'Announcement updated.',
        'Edit Announcement',
        'hostel:warden_announcements',
        instance=announcement,
    )


@_warden_required
def announcement_delete(request, pk):
    return _handle_delete(
        request,
        Announcement,
        pk,
        'hostel:warden_announcements',
        'Announcement removed.',
        'Announcement',
        'hostel:warden_announcements',
    )


# --- Warden Management Views: Menu ---

@_warden_required
def warden_menu(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'hostel/warden_menu.html', {
        'menu_items': menu_items,
    })


@_warden_required
def menu_create(request):
    return _handle_form(
        request,
        MenuItemForm,
        'hostel/entry_form.html',
        'hostel:warden_menu',
        'Menu entry added.',
        'Add Menu Entry',
        'hostel:warden_menu',
    )


@_warden_required
def menu_edit(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    return _handle_form(
        request,
        MenuItemForm,
        'hostel/entry_form.html',
        'hostel:warden_menu',
        'Menu entry updated.',
        'Edit Menu Entry',
        'hostel:warden_menu',
        instance=menu_item,
    )


@_warden_required
def menu_delete(request, pk):
    return _handle_delete(
        request,
        MenuItem,
        pk,
        'hostel:warden_menu',
        'Menu entry removed.',
        'Menu Entry',
        'hostel:warden_menu',
    )


# --- Warden Management Views: Rules ---

@_warden_required
def warden_rules(request):
    rules = Rule.objects.all()
    return render(request, 'hostel/warden_rules.html', {
        'rules': rules,
    })


@_warden_required
def rule_create(request):
    return _handle_form(
        request,
        RuleForm,
        'hostel/entry_form.html',
        'hostel:warden_rules',
        'Rule added.',
        'Add Rule',
        'hostel:warden_rules',
    )


@_warden_required
def rule_edit(request, pk):
    rule = get_object_or_404(Rule, pk=pk)
    return _handle_form(
        request,
        RuleForm,
        'hostel/entry_form.html',
        'hostel:warden_rules',
        'Rule updated.',
        'Edit Rule',
        'hostel:warden_rules',
        instance=rule,
    )


@_warden_required
def rule_delete(request, pk):
    return _handle_delete(
        request,
        Rule,
        pk,
        'hostel:warden_rules',
        'Rule removed.',
        'Rule',
        'hostel:warden_rules',
    )


# ==========================================
# Warden Student Registration & Management (VS-02)
# ==========================================

@warden_required
def warden_student_list(request):
    """List all registered students with room and fee overview."""
    students = student_service.list_students()
    records = []
    for s in students:
        room_info = room_service.get_student_room(s.student_id)
        ledger = finance_services.get_ledger(s.id)
        records.append({
            'student': s,
            'room': room_info,
            'ledger': ledger,
        })
    return render(request, 'hostel/warden_student_list.html', {
        'records': records,
    })


@warden_required
def warden_student_create(request):
    """Register a new student with login account, fee record and room assignment (FR-01)."""
    rooms = room_service.list_rooms()

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        contact_number = request.POST.get('contact_number', '').strip()
        guardian_name = request.POST.get('guardian_name', '').strip()
        guardian_contact_number = request.POST.get('guardian_contact_number', '').strip()
        room_identifier = request.POST.get('room', '').strip()
        total_fee = request.POST.get('total_fee', '').strip()
        opening_paid = request.POST.get('opening_paid', '0').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        temporary_password = request.POST.get('temporary_password', '').strip()

        try:
            result = student_service.register_student(
                full_name=full_name,
                student_id=student_id,
                contact_number=contact_number,
                guardian_name=guardian_name,
                guardian_contact_number=guardian_contact_number,
                room_identifier=room_identifier,
                total_fee=total_fee,
                opening_paid=opening_paid,
                email=email,
                address=address,
                temporary_password=temporary_password or None,
                created_by=request.user.username,
            )
            return render(request, 'hostel/warden_student_success.html', {
                'student': result['student'],
                'user': result['user'],
                'room': result['room'],
                'temporary_password': result['temporary_password'],
                'ledger': result['ledger'],
            })
        except (StudentError, RoomError) as exc:
            messages.error(request, str(exc))
            return render(request, 'hostel/warden_student_create.html', {
                'rooms': rooms,
                'form_data': request.POST,
            })

    return render(request, 'hostel/warden_student_create.html', {
        'rooms': rooms,
        'form_data': {},
    })


@warden_required
def warden_student_detail(request, pk):
    """View details of a student record."""
    student = get_object_or_404(Student, pk=pk)
    room_info = room_service.get_student_room(student.student_id)
    ledger = finance_services.get_ledger(student.id)
    fee_history = finance_services.get_history(student.id)

    return render(request, 'hostel/warden_student_detail.html', {
        'student': student,
        'room': room_info,
        'ledger': ledger,
        'fee_history': fee_history,
    })


@warden_required
def warden_room_create(request):
    """Quick room creation helper for warden if catalogue is empty."""
    if request.method == 'POST':
        room_number = request.POST.get('room_number', '').strip()
        capacity = request.POST.get('capacity', '').strip()
        try:
            room_service.create_room(room_number, capacity)
            messages.success(request, f'Room {room_number} created successfully.')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('hostel:warden_student_create')
        except RoomError as exc:
            messages.error(request, str(exc))

    return redirect('hostel:warden_student_create')

