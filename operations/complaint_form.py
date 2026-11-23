from django import forms

from .file_storage import (
    FileStorageError,
    FileTooLargeError,
    InvalidFileTypeError,
    validate_upload,
)
from .models import Complaint


class ComplaintForm(forms.Form):
    """Form for student complaint submission with optional validated attachment (FR-07, C-02)."""

    category = forms.ChoiceField(
        choices=[('', '---------')] + list(Complaint.CATEGORY_CHOICES),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
    )
    attachment = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    def clean_attachment(self):
        f = self.cleaned_data.get('attachment')
        if f:
            try:
                validate_upload(f)
            except (InvalidFileTypeError, FileTooLargeError, FileStorageError) as exc:
                raise forms.ValidationError(str(exc))
        return f
