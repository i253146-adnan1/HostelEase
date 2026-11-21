from django.contrib import admin

from .models import Announcement, MenuItem, Rule, Room, RoomAssignment, Student


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'message')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('day_of_week', 'meal_type', 'created_at')
    list_filter = ('day_of_week', 'meal_type')


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'capacity', 'created_at')
    search_fields = ('room_number',)


@admin.register(RoomAssignment)
class RoomAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'room', 'assigned_at', 'is_active')
    list_filter = ('is_active', 'room')
    search_fields = ('student_id', 'room__room_number')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'contact_number', 'guardian_name', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student_id', 'full_name', 'contact_number', 'guardian_name')

