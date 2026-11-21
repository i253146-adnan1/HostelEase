from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom HostelEase User model."""

    list_display = ('username', 'email', 'role', 'must_change_password', 'is_staff', 'is_active')
    list_filter = ('role', 'must_change_password', 'is_staff', 'is_active')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('HostelEase', {'fields': ('role', 'must_change_password', 'student_id')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('HostelEase', {'fields': ('role', 'must_change_password', 'student_id')}),
    )
