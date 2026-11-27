from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('warden/', views.warden_dashboard_view, name='warden_dashboard'),
    path('warden/language/', views.set_warden_language_view, name='set_warden_language'),
]
