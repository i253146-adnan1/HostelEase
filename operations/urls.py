from django.urls import path

from . import views

app_name = 'operations'

urlpatterns = [
    # Student feedback submission (FR-15, AC-15.1, AC-15.3)
    path('feedback/', views.student_feedback_view, name='student_feedback'),

    # Warden feedback rating summary (FR-15, AC-15.4)
    path('warden/feedback/', views.warden_feedback_summary_view, name='warden_feedback_summary'),

    # Shared authorization-checked file delivery (VS-08, ADR-004, NFR-01)
    path('files/<uuid:file_key>/', views.download_stored_file, name='download_file'),

    # Student complaint submission and status views (VS-10, FR-07)
    path('complaints/', views.student_complaint_list, name='complaint_list'),
    path('complaints/submit/', views.student_complaint_submit, name='complaint_submit'),
    path('complaints/<int:complaint_id>/', views.student_complaint_detail, name='complaint_detail'),
]
