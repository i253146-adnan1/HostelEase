from django.urls import path

from . import views

app_name = 'operations'

urlpatterns = [
    # Student feedback submission (FR-15, AC-15.1, AC-15.3)
    path('feedback/', views.student_feedback_view, name='student_feedback'),

    # Warden feedback rating summary (FR-15, AC-15.4)
    path('warden/feedback/', views.warden_feedback_summary_view, name='warden_feedback_summary'),
]
