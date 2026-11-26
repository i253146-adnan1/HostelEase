"""Service layer for user profile display picture (avatar) management."""

import os

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_AVATAR_FORMATS = {'JPEG', 'PNG', 'WEBP'}
MAX_AVATAR_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


def validate_avatar_file(uploaded_file):
    """Validate avatar file extension, size (<= 2 MB), and actual image integrity."""
    if uploaded_file is None:
        raise ValidationError('Please select an image file to upload.')

    ext = os.path.splitext(getattr(uploaded_file, 'name', '') or '')[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValidationError('Unsupported file format. Please upload a JPG, JPEG, PNG, or WEBP image.')

    if uploaded_file.size > MAX_AVATAR_SIZE_BYTES:
        raise ValidationError('File size exceeds the 2 MB limit.')

    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as img:
            img_format = (img.format or '').upper()
            img.verify()
        if img_format not in ALLOWED_AVATAR_FORMATS:
            raise ValidationError('Unsupported image format. Please upload a valid JPG, PNG, or WEBP image.')
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError('The uploaded file is not a valid image.') from exc
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass


def update_user_avatar(user, uploaded_file):
    """Validate and save a new display picture for the given user, deleting any old file."""
    validate_avatar_file(uploaded_file)

    old_name = user.avatar.name if user.avatar else None
    storage = user.avatar.storage if user.avatar else None

    user.avatar = uploaded_file
    user.save(update_fields=['avatar'])

    if old_name and old_name != user.avatar.name and storage is not None:
        if storage.exists(old_name):
            storage.delete(old_name)

    return user.avatar


def remove_user_avatar(user):
    """Remove the current user's display picture and delete its file from local storage."""
    if not user.avatar:
        return False

    old_name = user.avatar.name
    storage = user.avatar.storage

    user.avatar = None
    user.save(update_fields=['avatar'])

    if old_name and storage.exists(old_name):
        storage.delete(old_name)

    return True
