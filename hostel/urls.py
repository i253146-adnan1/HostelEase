from django.urls import path
from . import views

app_name = 'hostel'

urlpatterns = [
    # Student read-only hostel info (VS-06)
    path('announcements/', views.student_announcements, name='student_announcements'),
    path('menu/', views.student_menu, name='student_menu'),
    path('rules/', views.student_rules, name='student_rules'),

    # Warden announcements CRUD (VS-06)
    path('warden/announcements/', views.warden_announcements, name='warden_announcements'),
    path('warden/announcements/create/', views.announcement_create, name='announcement_create'),
    path('warden/announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('warden/announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

    # Warden menu CRUD (VS-06)
    path('warden/menu/', views.warden_menu, name='warden_menu'),
    path('warden/menu/create/', views.menu_create, name='menu_create'),
    path('warden/menu/<int:pk>/edit/', views.menu_edit, name='menu_edit'),
    path('warden/menu/<int:pk>/delete/', views.menu_delete, name='menu_delete'),

    # Warden rules CRUD (VS-06)
    path('warden/rules/', views.warden_rules, name='warden_rules'),
    path('warden/rules/create/', views.rule_create, name='rule_create'),
    path('warden/rules/<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    path('warden/rules/<int:pk>/delete/', views.rule_delete, name='rule_delete'),

    # Room management (VS-03)
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/<int:room_id>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<int:room_id>/delete/', views.room_delete, name='room_delete'),
    path('rooms/<int:room_id>/assign/', views.room_assign, name='room_assign'),
    path('rooms/assignment/<int:assignment_id>/clear/', views.room_clear_assignment, name='room_clear_assignment'),

    # Warden student registration & management (VS-02)
    path('warden/students/', views.warden_student_list, name='warden_student_list'),
    path('warden/students/create/', views.warden_student_create, name='warden_student_create'),
    path('warden/students/<int:pk>/', views.warden_student_detail, name='warden_student_detail'),
]
