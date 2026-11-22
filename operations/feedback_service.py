"""Feedback service interface (VS-07).

Encapsulates star-rating submission and warden aggregation summary.
Owns Feedback data and respects module boundaries (no cross-module FKs).

Invariants:
- 1 to 5 stars only (AC-15.1, AC-15.2).
- Non-integer or out-of-range values rejected (AC-15.2).
- Repeated submissions allowed, creating distinct retained records (AC-15.3, BR-05).
- Feedback records are immutable once saved (BR-11).
- Warden summary aggregates counts per star level per aspect (AC-15.4).
"""
from django.db import transaction
from django.db.models import Avg, Count, Q

from .models import Feedback


class FeedbackError(Exception):
    """Base exception for Feedback operations."""


class FeedbackValidationError(FeedbackError):
    """Validation failure in feedback inputs."""


ASPECTS = [
    ('food', 'Food & Mess', 'food_rating'),
    ('room', 'Rooms & Maintenance', 'room_rating'),
    ('washroom', 'Washrooms & Cleanliness', 'washroom_rating'),
    ('environment', 'Hostel Environment', 'environment_rating'),
]


def validate_star_rating(value, label='Rating'):
    """Validate that a rating is an integer between 1 and 5."""
    if value is None or str(value).strip() == '':
        raise FeedbackValidationError(f'{label} rating is required.')

    try:
        val = int(value)
    except (TypeError, ValueError):
        raise FeedbackValidationError(f'{label} rating must be a whole number between 1 and 5.')

    if val < 1 or val > 5:
        raise FeedbackValidationError(f'{label} rating must be between 1 and 5 stars.')

    return val


@transaction.atomic
def submit_feedback(student_id, food, room, washroom, environment):
    """Submit 1-5 star ratings for the 4 aspects (FR-15, AC-15.1).

    Repeat submissions create separate entries (AC-15.3).
    """
    sid = str(student_id or '').strip()
    if not sid:
        raise FeedbackValidationError('Student ID is required.')

    f_rate = validate_star_rating(food, 'Food')
    r_rate = validate_star_rating(room, 'Room')
    w_rate = validate_star_rating(washroom, 'Washroom')
    e_rate = validate_star_rating(environment, 'Environment')

    return Feedback.objects.create(
        student_id=sid,
        food_rating=f_rate,
        room_rating=r_rate,
        washroom_rating=w_rate,
        environment_rating=e_rate,
    )


def list_student_feedback(student_id):
    """Return past feedback submissions for a student (read-only history)."""
    sid = str(student_id or '').strip()
    return Feedback.objects.filter(student_id=sid).order_by('-created_at')


def get_feedback_summary():
    """Aggregate rating counts (1 to 5 stars) and averages for each aspect (AC-15.4)."""
    total_submissions = Feedback.objects.count()

    summary = {
        'total_submissions': total_submissions,
        'aspects': {},
    }

    for key, display_name, field_name in ASPECTS:
        counts = {}
        for star in range(1, 6):
            counts[star] = Feedback.objects.filter(**{field_name: star}).count()

        avg_rating = Feedback.objects.aggregate(avg=Avg(field_name))['avg'] or 0.0

        percentages = {}
        for star in range(1, 6):
            if total_submissions > 0:
                percentages[star] = round((counts[star] / total_submissions) * 100, 1)
            else:
                percentages[star] = 0.0

        summary['aspects'][key] = {
            'label': display_name,
            'field': field_name,
            'counts': counts,
            'percentages': percentages,
            'average': round(float(avg_rating), 2),
        }

    return summary
