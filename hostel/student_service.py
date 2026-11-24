"""Student Management service interface (VS-02).

Owns student records, registration workflow, and identity validation.
Interacts with:
- Accounts (User creation and credential management)
- Rooms (RoomService for room assignment and capacity check)
- Finance (create_fee_record for initial fee and opening balance)

Invariants:
- Mandatory fields required (FR-01, AC-01.3).
- Student ID must be unique (AC-01.2, EC-01).
- Room capacity must not be exceeded (AC-01.4, BR-06, OQ-21).
- Entire registration is atomic; failures roll back completely (OQ-21, EC-30, EC-31).
- One-time temporary password issued; must change on first login (AC-01.1, AC-02.4, OQ-25).
"""
import re
import secrets
import string

from django.contrib.auth import get_user_model
from django.db import transaction

from finance import services as finance_services
from finance.services import FeeError
from . import room_service
from .models import Student
from .room_service import RoomError, RoomFullError, RoomNotFoundError

User = get_user_model()


class StudentError(Exception):
    """Base exception for Student Management errors."""


class StudentValidationError(StudentError):
    """Validation failure in student fields."""


class DuplicateStudentError(StudentError):
    """Student ID already registered."""


def validate_contact_number(number, label='Contact number'):
    """Validate contact number format and digit length (10 to 15 digits)."""
    text = str(number or '').strip()
    if not text:
        raise StudentValidationError(f'{label} is required.')

    # Allowed characters: digits, spaces, hyphens, optional leading '+'
    if not re.match(r'^\+?[0-9\s\-]+$', text):
        raise StudentValidationError(f'{label} is invalid. Only numbers, spaces, and hyphens are allowed.')

    digits = re.sub(r'\D', '', text)
    if len(digits) < 10 or len(digits) > 15:
        raise StudentValidationError(f'{label} must contain between 10 and 15 digits.')

    return text


def exists(student_id):
    """Check if student ID exists (VS-03 and Visitor Log dependency)."""
    sid = str(student_id or '').strip()
    if not sid:
        return False
    return Student.objects.filter(student_id=sid).exists()


def get_student_by_id(student_id):
    """Retrieve Student record by student_id string."""
    sid = str(student_id or '').strip()
    return Student.objects.filter(student_id=sid).first()


def validate_active_student(student_id: str) -> dict | None:
    """Validate that student_id belongs to an Active student.

    Looks up Student by Student.student_id (roll/hostel ID, not user.pk).
    Returns None if not found or status != 'Active'; otherwise returns
    {'student_id': student.student_id, 'status': student.status, 'user_id': student.user_id}.
    """
    sid = str(student_id or '').strip()
    if not sid:
        return None
    student = Student.objects.filter(student_id=sid).first()
    if not student or student.status != Student.STATUS_ACTIVE:
        return None
    return {
        'student_id': student.student_id,
        'status': student.status,
        'user_id': student.user_id,
    }


class StudentService:
    """Bridge interface for cross-module student lookups (AGENTS.md)."""

    @staticmethod
    def validate_active_student(student_id: str) -> dict | None:
        return validate_active_student(student_id)


def get_student(pk):
    """Retrieve Student record by primary key."""
    return Student.objects.filter(pk=pk).first()


def list_students():
    """Return all students ordered by student_id."""
    return Student.objects.all().order_by('student_id')


def generate_temporary_password(length=12):
    """Generate a secure temporary password meeting standard password rules."""
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = '!@#$%^&*'
    alphabet = upper + lower + digits + special

    # Ensure at least one character from each set
    pwd = [
        secrets.choice(upper),
        secrets.choice(lower),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    pwd += [secrets.choice(alphabet) for _ in range(max(length - 4, 8))]
    secrets.SystemRandom().shuffle(pwd)
    return ''.join(pwd)


@transaction.atomic
def register_student(
    full_name,
    student_id,
    contact_number,
    guardian_name,
    guardian_contact_number,
    room_identifier,
    total_fee,
    opening_paid=0,
    email='',
    address='',
    temporary_password=None,
    created_by='',
):
    """Register student, create auth account, assign room, and create fee record.

    Atomic execution: rolls back all changes if any step fails (AC-01.1-AC-01.4, OQ-21).
    """
    fname = str(full_name or '').strip()
    sid = str(student_id or '').strip()
    cnum = str(contact_number or '').strip()
    gname = str(guardian_name or '').strip()
    gcnum = str(guardian_contact_number or '').strip()
    room_ref = str(room_identifier if room_identifier is not None else '').strip()

    # 1. Mandatory field checks
    if not fname:
        raise StudentValidationError('Full name is required.')
    if not sid:
        raise StudentValidationError('Student ID is required.')
    if not cnum:
        raise StudentValidationError('Contact number is required.')
    if not gname:
        raise StudentValidationError('Guardian name is required.')
    if not gcnum:
        raise StudentValidationError('Guardian contact number is required.')
    if not room_ref:
        raise StudentValidationError('Room selection is required.')

    # 2. Contact numbers validation
    validate_contact_number(cnum, 'Contact number')
    validate_contact_number(gcnum, 'Guardian contact number')

    # 3. Uniqueness checks
    if Student.objects.filter(student_id=sid).exists():
        raise DuplicateStudentError(f"A student with ID '{sid}' already exists.")
    if User.objects.filter(username=sid).exists():
        raise DuplicateStudentError(f"A user account with username '{sid}' already exists.")

    # 4. Total fee / opening paid validation (delegated to finance service)
    try:
        parsed_total = finance_services.parse_money(total_fee, 'Total fee')
        parsed_opening = finance_services.parse_money(
            opening_paid if opening_paid not in (None, '') else 0,
            'Opening paid amount'
        )
    except FeeError as exc:
        raise StudentValidationError(str(exc)) from exc

    # 5. Room assignment & capacity check (RoomService)
    try:
        assignment = room_service.assign_student(student_id=sid, room_identifier=room_ref)
    except (RoomFullError, RoomNotFoundError, RoomError) as exc:
        raise StudentValidationError(str(exc)) from exc

    # 6. User account creation (one-time temporary password, must_change_password=True)
    temp_pwd = str(temporary_password).strip() if temporary_password and str(temporary_password).strip() else generate_temporary_password()
    user = User.objects.create_user(
        username=sid,
        password=temp_pwd,
        role='student',
        student_id=sid,
        must_change_password=True,
        email=str(email or '').strip(),
    )

    # 7. Student record creation
    student = Student.objects.create(
        student_id=sid,
        full_name=fname,
        contact_number=cnum,
        guardian_name=gname,
        guardian_contact_number=gcnum,
        email=str(email or '').strip(),
        address=str(address or '').strip(),
        status=Student.STATUS_ACTIVE,
        user_id=user.id,
    )

    # 8. Initial Fee record creation (finance service)
    try:
        ledger = finance_services.create_fee_record(
            student_ref=student.id,
            total_fee=parsed_total,
            opening_paid=parsed_opening,
            changed_by=created_by or 'warden',
        )
    except FeeError as exc:
        raise StudentValidationError(str(exc)) from exc

    return {
        'student': student,
        'user': user,
        'room_assignment': assignment,
        'room': assignment.room,
        'temporary_password': temp_pwd,
        'ledger': ledger,
    }


def _sync_account_student_profile(user, status, room_number=None):
    """Keep optional accounts.StudentProfile in sync if present."""
    try:
        from accounts.models import StudentProfile
        profile = StudentProfile.objects.filter(user=user).first()
        if profile is not None:
            profile.status = status
            if room_number is not None:
                profile.room_number = room_number
            profile.save(update_fields=['status', 'room_number', 'updated_at'])
    except ImportError:
        pass


@transaction.atomic
def mark_student_left(student_pk):
    """Mark an Active student Left: disable login, clear room, retain all records (VS-16, FR-13, AC-13.1)."""
    student = Student.objects.select_for_update().filter(pk=student_pk).first()
    if student is None:
        raise StudentError('Student record not found.')
    if student.status == Student.STATUS_LEFT:
        raise StudentValidationError('Student is already marked Left.')

    student.status = Student.STATUS_LEFT
    student.save(update_fields=['status', 'updated_at'])

    # Clear active room assignment while retaining historical RoomAssignment rows
    room_service.clear_student_room(student.student_id)

    # Disable future login (OQ-13)
    user = None
    if student.user_id:
        user = User.objects.filter(pk=student.user_id).first()
    if user is None:
        user = User.objects.filter(username=student.student_id).first()
    if user is not None:
        user.is_active = False
        user.save(update_fields=['is_active'])
        _sync_account_student_profile(user, Student.STATUS_LEFT, room_number='')

    return student


@transaction.atomic
def reactivate_student(student_pk):
    """Reactivate a Left student: re-enable login on same record, keep room empty (VS-16, FR-13, AC-13.3)."""
    student = Student.objects.select_for_update().filter(pk=student_pk).first()
    if student is None:
        raise StudentError('Student record not found.')
    if student.status == Student.STATUS_ACTIVE:
        raise StudentValidationError('Student is already Active.')

    student.status = Student.STATUS_ACTIVE
    student.save(update_fields=['status', 'updated_at'])

    user = None
    if student.user_id:
        user = User.objects.filter(pk=student.user_id).first()
    if user is None:
        user = User.objects.filter(username=student.student_id).first()
    if user is not None:
        user.is_active = True
        user.save(update_fields=['is_active'])
        _sync_account_student_profile(user, Student.STATUS_ACTIVE, room_number='')

    return student
