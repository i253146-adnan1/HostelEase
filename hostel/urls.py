from django.urls import path

from . import views

app_name = 'hostel'

urlpatterns = [
    # Student read-only views
    path('announcements/', views.student_announcements, name='student_announcements'),
    path('menu/', views.student_menu, name='student_menu'),
    path('rules/', views.student_rules, name='student_rules'),

    # Warden announcements CRUD
    path('warden/announcements/', views.warden_announcements, name='warden_announcements'),
    path('warden/announcements/create/', views.announcement_create, name='announcement_create'),
    path('warden/announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('warden/announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

    # Warden menu CRUD
    path('warden/menu/', views.warden_menu, name='warden_menu'),
    path('warden/menu/create/', views.menu_create, name='menu_create'),
    path('warden/menu/<int:pk>/edit/', views.menu_edit, name='menu_edit'),
    path('warden/menu/<int:pk>/delete/', views.menu_delete, name='menu_delete'),

    # Warden rules CRUD
    path('warden/rules/', views.warden_rules, name='warden_rules'),
    path('warden/rules/create/', views.rule_create, name='rule_create'),
    path('warden/rules/<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    path('warden/rules/<int:pk>/delete/', views.rule_delete, name='rule_delete'),
]
