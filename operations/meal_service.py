"""Meal opt-out service interface (VS-18, FR-19, AC-19.1-AC-19.5, EC-50, EC-51, OQ-33).

Kept separate from the warden pending-items dashboard per ADR-005.
"""
from datetime import date, datetime

from django.db.models import Count, Q
from django.utils import timezone

from .models import MealOptOut


class MealOptOutError(Exception):
    """Business-rule or validation error for meal opt-outs."""


def parse_meal_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or '').strip()
    if not text:
        raise MealOptOutError('Meal date is required.')
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise MealOptOutError('Meal date must be a valid date (YYYY-MM-DD).')


def create_opt_out(*, student_id, meal_date, meal_type, today=None):
    """Create an Active meal opt-out for a non-past date (AC-19.1, AC-19.2, EC-50)."""
    sid = str(student_id or '').strip()
    if not sid:
        raise MealOptOutError('Student ID is required.')

    valid_meals = dict(MealOptOut.MEAL_CHOICES)
    meal = str(meal_type or '').strip()
    if meal not in valid_meals:
        raise MealOptOutError('Please select Breakfast, Lunch, or Dinner.')

    parsed_date = parse_meal_date(meal_date)
    ref_today = today if today is not None else timezone.localdate()
    if parsed_date < ref_today:
        raise MealOptOutError('Cannot opt out of a meal for a past date.')

    if MealOptOut.objects.filter(
        student_id=sid,
        meal_date=parsed_date,
        meal_type=meal,
        status=MealOptOut.STATUS_ACTIVE,
    ).exists():
        raise MealOptOutError(f'You already have an Active opt-out for {meal} on {parsed_date}.')

    return MealOptOut.objects.create(
        student_id=sid,
        meal_date=parsed_date,
        meal_type=meal,
        status=MealOptOut.STATUS_ACTIVE,
    )


def cancel_opt_out(*, opt_out_id, student_id, today=None):
    """Cancel an Active opt-out before its meal date has passed (AC-19.3, AC-19.4, EC-51)."""
    sid = str(student_id or '').strip()
    opt_out = MealOptOut.objects.filter(pk=opt_out_id, student_id=sid).first()
    if opt_out is None:
        raise MealOptOutError('Meal opt-out record not found.')

    if opt_out.status != MealOptOut.STATUS_ACTIVE:
        raise MealOptOutError('This opt-out is already cancelled.')

    ref_today = today if today is not None else timezone.localdate()
    if opt_out.meal_date < ref_today:
        raise MealOptOutError('Cannot cancel an opt-out after the meal date has passed.')

    opt_out.status = MealOptOut.STATUS_CANCELLED
    opt_out.cancelled_at = timezone.now()
    opt_out.save(update_fields=['status', 'cancelled_at'])
    return opt_out


def list_student_opt_outs(student_id):
    sid = str(student_id or '').strip()
    return list(MealOptOut.objects.filter(student_id=sid))


def get_warden_opt_out_summary(filter_date=None):
    """Aggregate Active opt-outs per date and meal type (AC-19.5)."""
    qs = MealOptOut.objects.filter(status=MealOptOut.STATUS_ACTIVE)
    if filter_date not in (None, ''):
        qs = qs.filter(meal_date=parse_meal_date(filter_date))

    rows = (
        qs.values('meal_date')
        .annotate(
            breakfast=Count('id', filter=Q(meal_type=MealOptOut.MEAL_BREAKFAST)),
            lunch=Count('id', filter=Q(meal_type=MealOptOut.MEAL_LUNCH)),
            dinner=Count('id', filter=Q(meal_type=MealOptOut.MEAL_DINNER)),
            total=Count('id'),
        )
        .order_by('meal_date')
    )
    return list(rows)
