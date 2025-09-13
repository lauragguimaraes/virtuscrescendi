from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'nome', 'email', 'role', 'empregado_id', 
        'is_active', 'two_factor_status', 'last_login'
    ]
    list_filter = ['role', 'is_active', 'two_factor_enabled', 'date_joined']
    search_fields = ['username', 'nome', 'email', 'empregado_id']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {
            'fields': ('nome', 'first_name', 'last_name', 'email', 'telefone')
        }),
        ('Informações Profissionais', {
            'fields': ('role', 'empregado_id')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('2FA', {
            'fields': ('two_factor_enabled', 'totp_secret'),
            'classes': ('collapse',)
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'nome', 'email', 'role', 'empregado_id', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at']
    
    def two_factor_status(self, obj):
        if obj.is_chefe:
            if obj.two_factor_enabled:
                return format_html(
                    '<span class="badge" style="background-color: #198754; color: white;">Habilitado</span>'
                )
            else:
                return format_html(
                    '<span class="badge" style="background-color: #ffc107; color: black;">Não Configurado</span>'
                )
        return format_html(
            '<span class="badge" style="background-color: #6c757d; color: white;">N/A</span>'
        )
    two_factor_status.short_description = '2FA'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'table_name', 'record_id', 'ip_address']
    list_filter = ['action', 'table_name', 'timestamp']
    search_fields = ['user__nome', 'user__username', 'table_name', 'record_id', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'action', 'table_name', 'record_id', 'old_value', 'new_value', 'ip_address', 'user_agent']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Logs são criados automaticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs são imutáveis
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Logs não podem ser deletados
        return False
