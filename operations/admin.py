from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'food_rating',
        'room_rating',
        'washroom_rating',
        'environment_rating',
        'created_at',
    )
    list_filter = (
        'food_rating',
        'room_rating',
        'washroom_rating',
        'environment_rating',
        'created_at',
    )
    search_fields = ('student_id',)
    readonly_fields = (
        'student_id',
        'food_rating',
        'room_rating',
        'washroom_rating',
        'environment_rating',
        'created_at',
    )

    def has_add_permission(self, request):
        # Feedback is submitted by students only
        return False

    def has_delete_permission(self, request, obj=None):
        # BR-05: Feedback records are retained
        return False
