from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Unit, Substance, SubstanceUnitConfig, Patient, Batch, 
    Inventory, StockMovement, UnitTransfer
)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'responsavel', 'telefone', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'codigo', 'responsavel']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'codigo', 'responsavel')
        }),
        ('Contato', {
            'fields': ('endereco', 'telefone', 'email')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Substance)
class SubstanceAdmin(admin.ModelAdmin):
    list_display = [
        'nome_comum', 'nome_comercial', 'concentracao', 'apresentacao', 
        'unidade', 'estoque_total_display', 'estoque_minimo_default', 'status_estoque'
    ]
    list_filter = ['unidade', 'created_at']
    search_fields = ['nome_comum', 'nome_comercial', 'concentracao']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_comum', 'nome_comercial', 'concentracao', 'apresentacao', 'unidade')
        }),
        ('Configurações de Alerta', {
            'fields': ('estoque_minimo_default', 'dias_alerta_vencimento')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def estoque_total_display(self, obj):
        estoque = obj.get_estoque_total()
        if obj.estoque_baixo:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                estoque
            )
        return estoque
    estoque_total_display.short_description = 'Estoque Total'
    
    def status_estoque(self, obj):
        if obj.estoque_baixo:
            return format_html(
                '<span class="badge" style="background-color: #dc3545; color: white;">Baixo</span>'
            )
        return format_html(
            '<span class="badge" style="background-color: #198754; color: white;">OK</span>'
        )
    status_estoque.short_description = 'Status'


@admin.register(SubstanceUnitConfig)
class SubstanceUnitConfigAdmin(admin.ModelAdmin):
    list_display = ['substance', 'unit', 'estoque_minimo', 'ativo']
    list_filter = ['unit', 'ativo', 'created_at']
    search_fields = ['substance__nome_comum', 'unit__nome']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'unidade_principal', 'telefone', 'ativo', 'created_at']
    list_filter = ['unidade_principal', 'ativo', 'created_at']
    search_fields = ['codigo', 'nome', 'telefone', 'email']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'nome', 'data_nascimento', 'unidade_principal')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = [
        'lote', 'substance', 'unit', 'validade', 'quantidade_recebida', 
        'fornecedor', 'status_validade', 'preco_total'
    ]
    list_filter = ['unit', 'substance', 'validade', 'created_at']
    search_fields = ['lote', 'substance__nome_comum', 'fornecedor']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'preco_total']
    
    fieldsets = (
        ('Informações do Lote', {
            'fields': ('substance', 'unit', 'lote', 'validade', 'quantidade_recebida')
        }),
        ('Fornecedor', {
            'fields': ('fornecedor', 'nota_fiscal_ref', 'preco_unitario', 'preco_total')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_validade(self, obj):
        if obj.vencido:
            return format_html(
                '<span class="badge" style="background-color: #dc3545; color: white;">Vencido</span>'
            )
        elif obj.vencendo_em_breve:
            return format_html(
                '<span class="badge" style="background-color: #ffc107; color: black;">Vencendo</span>'
            )
        return format_html(
            '<span class="badge" style="background-color: #198754; color: white;">OK</span>'
        )
    status_validade.short_description = 'Status Validade'


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = [
        'substance', 'batch', 'unit', 'quantity_on_hand', 
        'status_estoque', 'updated_at'
    ]
    list_filter = ['unit', 'substance', 'updated_at']
    search_fields = ['substance__nome_comum', 'batch__lote', 'unit__nome']
    readonly_fields = ['created_at', 'updated_at']
    
    def status_estoque(self, obj):
        if obj.estoque_baixo:
            return format_html(
                '<span class="badge" style="background-color: #dc3545; color: white;">Baixo</span>'
            )
        return format_html(
            '<span class="badge" style="background-color: #198754; color: white;">OK</span>'
        )
    status_estoque.short_description = 'Status'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'data_hora', 'tipo', 'substance', 'batch', 'unit', 
        'quantidade', 'user', 'paciente_nome'
    ]
    list_filter = ['tipo', 'unit', 'substance', 'data_hora']
    search_fields = [
        'substance__nome_comum', 'batch__lote', 'paciente_nome', 
        'user__username', 'motivo'
    ]
    readonly_fields = [
        'data_hora', 'user', 'ip_address', 'user_agent'
    ]
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('substance', 'batch', 'unit', 'tipo', 'quantidade', 'motivo')
        }),
        ('Paciente', {
            'fields': ('paciente', 'paciente_nome', 'procedimento')
        }),
        ('Transferência', {
            'fields': ('unidade_destino',)
        }),
        ('Auditoria', {
            'fields': ('data_hora', 'user', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UnitTransfer)
class UnitTransferAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'unidade_origem', 'unidade_destino', 'substance', 
        'quantidade', 'status', 'data_solicitacao'
    ]
    list_filter = ['status', 'unidade_origem', 'unidade_destino', 'data_solicitacao']
    search_fields = ['codigo', 'substance__nome_comum', 'motivo']
    readonly_fields = [
        'data_solicitacao', 'data_envio', 'data_recebimento',
        'solicitado_por', 'enviado_por', 'recebido_por'
    ]
    
    fieldsets = (
        ('Transferência', {
            'fields': ('codigo', 'unidade_origem', 'unidade_destino', 'substance', 'batch', 'quantidade')
        }),
        ('Detalhes', {
            'fields': ('motivo', 'status')
        }),
        ('Datas', {
            'fields': ('data_solicitacao', 'data_envio', 'data_recebimento')
        }),
        ('Responsáveis', {
            'fields': ('solicitado_por', 'enviado_por', 'recebido_por'),
            'classes': ('collapse',)
        }),
    )

