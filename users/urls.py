from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('setup-2fa/', views.setup_2fa_view, name='setup_2fa'),
    path('audit-logs/', views.AuditLogView.as_view(), name='audit_logs'),
    path('verify-2fa/', views.verify_2fa_ajax, name='verify_2fa_ajax'),
]

