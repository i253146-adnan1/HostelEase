from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('profile/avatar/', views.avatar_settings_view, name='avatar_settings'),
    path('profile/avatar/upload/', views.avatar_upload_view, name='avatar_upload'),
    path('profile/avatar/remove/', views.avatar_remove_view, name='avatar_remove'),
    path('change-password/', views.change_password_view, name='change_password'),
]
