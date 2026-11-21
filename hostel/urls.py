from django.urls import path
from . import views

app_name = 'hostel'

urlpatterns = [
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/<int:room_id>/edit/', views.room_edit, name='room_edit'),
    path('rooms/<int:room_id>/delete/', views.room_delete, name='room_delete'),
    path('rooms/<int:room_id>/assign/', views.room_assign, name='room_assign'),
    path('rooms/assignment/<int:assignment_id>/clear/', views.room_clear_assignment, name='room_clear_assignment'),
]
