"""Shared local file-storage service (VS-08, FR-04, FR-07, C-02, NFR-01, ADR-004).

All payment proofs and optional complaint attachments are validated here, stored on
the local filesystem under ``settings.PRIVATE_UPLOAD_ROOT`` with UUID filenames, and
delivered only through an authorization-checked application route.
"""
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .models import StoredFile

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB (C-02)

ALLOWED_EXTENSIONS = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.pdf': 'application/pdf',
}

MAGIC_PREFIXES = {
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.png': (b'\x89PNG\r\n\x1a\n',),
    '.pdf': (b'%PDF-',),
}


class FileStorageError(Exception):
    """Base error for shared file-storage operations."""


class InvalidFileTypeError(FileStorageError):
    """Raised when extension or file header is not JPG, PNG, or PDF."""


class FileTooLargeError(FileStorageError):
    """Raised when file exceeds 5 MB or is empty."""


def get_upload_root():
    root = Path(getattr(settings, 'PRIVATE_UPLOAD_ROOT', Path(settings.BASE_DIR) / 'private_uploads'))
    return root.resolve()


def _read_header(uploaded_file, length=8):
    pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else None
    try:
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        header = uploaded_file.read(length)
    finally:
        if pos is not None and hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(pos)
    return header or b''


def validate_upload(uploaded_file):
    """Validate uploaded file extension, magic bytes, and 5 MB size limit (C-02)."""
    if uploaded_file is None:
        raise FileStorageError('No file provided.')

    raw_name = os.path.basename(getattr(uploaded_file, 'name', '') or '')
    ext = os.path.splitext(raw_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError('Only JPG, PNG, and PDF files are allowed.')

    size = getattr(uploaded_file, 'size', None)
    if size is None:
        raise FileStorageError('Unable to determine file size.')
    if size <= 0:
        raise FileTooLargeError('Uploaded file cannot be empty.')
    if size > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError('File size must be 5 MB or less.')

    header = _read_header(uploaded_file, 8)
    expected_prefixes = MAGIC_PREFIXES[ext]
    if not any(header.startswith(prefix) for prefix in expected_prefixes):
        raise InvalidFileTypeError('File content does not match an allowed JPG, PNG, or PDF format.')

    return ext, ALLOWED_EXTENSIONS[ext], raw_name[:255]


def save_uploaded_file(uploaded_file, *, category, owner_user_id, record_ref=''):
    """Validate and save a file locally, returning its ``StoredFile`` DB record."""
    valid_categories = dict(StoredFile.CATEGORY_CHOICES)
    if category not in valid_categories:
        raise FileStorageError('Invalid upload category.')
    if not owner_user_id:
        raise FileStorageError('Owner user ID is required.')

    ext, content_type, safe_original_name = validate_upload(uploaded_file)
    root = get_upload_root()
    category_dir = (root / category).resolve()
    if root not in category_dir.parents and category_dir != root:
        raise FileStorageError('Invalid storage directory.')
    category_dir.mkdir(parents=True, exist_ok=True)

    file_key = uuid.uuid4()
    stored_filename = f'{file_key.hex}{ext}'
    target_path = (category_dir / stored_filename).resolve()
    if category_dir not in target_path.parents:
        raise FileStorageError('Invalid target file path.')

    rel_path = f'{category}/{stored_filename}'

    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)

    with open(target_path, 'wb') as destination:
        if hasattr(uploaded_file, 'chunks'):
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        else:
            destination.write(uploaded_file.read())

    try:
        with transaction.atomic():
            return StoredFile.objects.create(
                file_key=file_key,
                category=category,
                owner_user_id=owner_user_id,
                record_ref=str(record_ref or '')[:64],
                original_name=safe_original_name,
                relative_path=rel_path,
                content_type=content_type,
                size_bytes=uploaded_file.size,
            )
    except Exception:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise


def get_stored_file(file_key):
    return StoredFile.objects.filter(file_key=file_key).first()


def resolve_stored_path(stored_file):
    root = get_upload_root()
    target = (root / stored_file.relative_path).resolve()
    if root not in target.parents:
        raise FileStorageError('Stored file path escapes upload root.')
    return target


def open_stored_file(stored_file):
    target = resolve_stored_path(stored_file)
    if not target.is_file():
        raise FileNotFoundError('Stored file is missing on disk.')
    return open(target, 'rb')


def can_access_file(user, stored_file):
    """Only the warden or the file's owning student may access the file (NFR-01)."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'role', None) == 'warden' or user.is_staff or user.is_superuser:
        return True
    return stored_file.owner_user_id == user.pk
