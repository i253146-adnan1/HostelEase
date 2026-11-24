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

    # Warden complaint management (VS-13, FR-08)
    path('warden/complaints/', views.warden_complaint_list, name='warden_complaint_list'),
    path('warden/complaints/<int:complaint_id>/', views.warden_complaint_detail, name='warden_complaint_detail'),
    path('warden/complaints/<int:complaint_id>/update/', views.warden_complaint_update_status, name='warden_complaint_update'),

    # Student temporary leave requests (VS-15, FR-17, BR-12, OQ-30)
    path('leave-requests/', views.student_leave_requests, name='student_leave_requests'),
    path('leave-requests/new/', views.student_leave_request_create, name='student_leave_request_create'),

    # Warden leave request review queue (VS-15, FR-17, AC-17.4)
    path('warden/leave-requests/', views.warden_leave_requests, name='warden_leave_requests'),
    path('warden/leave-requests/<int:request_id>/decide/', views.warden_decide_leave_request, name='warden_decide_leave_request'),
]
