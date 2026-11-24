from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.fee_list, name='list'),
    path('pending/', views.pending_payments_list, name='pending_payments'),
    path('<int:student_pk>/', views.fee_detail, name='detail'),
    path('payments/<int:payment_id>/verify/', views.verify_payment_action, name='verify_payment'),
    path('payments/<int:payment_id>/reject/', views.reject_payment_action, name='reject_payment'),
]
