from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.fee_list, name='list'),
    path('<int:student_pk>/', views.fee_detail, name='detail'),
]
