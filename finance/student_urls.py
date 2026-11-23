from django.urls import path

from . import views

app_name = 'finance_student'

urlpatterns = [
    path('my/', views.student_fee_and_proofs, name='my_fees'),
]
