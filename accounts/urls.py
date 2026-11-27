from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/<str:student_id>/reset-password/', views.student_reset_password_view, name='student_reset_password'),
    path('warden/manage/', views.warden_list_view, name='warden_list'),
    path('warden/create/', views.warden_create_view, name='warden_create'),
    path('warden/<int:pk>/reset-password/', views.warden_reset_password_view, name='warden_reset_password'),
    path('warden/profile/', views.warden_profile_view, name='warden_profile'),
    path('profile/avatar/', views.avatar_settings_view, name='avatar_settings'),
    path('profile/avatar/upload/', views.avatar_upload_view, name='avatar_upload'),
    path('profile/avatar/remove/', views.avatar_remove_view, name='avatar_remove'),
    path('change-password/', views.change_password_view, name='change_password'),
]
