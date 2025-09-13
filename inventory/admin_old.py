from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Substance, Batch, Inventory, StockMovement, Patient


@admin.register(Substance)
class SubstanceAdmin(admin.ModelAdmin):
    list_display = [
        'nome_comum', 'nome_comercial', 'concentracao', 'apresentacao', 
        'unidade', 'estoque_atual_display', 'estoque_minimo', 'status_estoque'
    ]
    list_filter = ['unidade', 'created_at']
    search_fields = ['nome_comum', 'nome_comercial', 'concentracao']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_comum', 'nome_comercial', 'concentracao', 'apresentacao', 'unidade')
        }),
        ('Configurações de Alerta', {
            'fields': ('estoque_minimo', 'dias_alerta_vencimento')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def estoque_atual_display(self, obj):
        estoque = obj.estoque_atual
        if estoque < obj.estoque_minimo:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                estoque
            )
        return estoque
    estoque_atual_display.short_description = 'Estoque Atual'
    
    def status_estoque(self, obj):
        if obj.estoque_baixo:
            return format_html(
                '<span class="badge" style="background-color: #dc3545; color: white;">Baixo</span>'
            )
        return format_html(
            '<span class="badge" style="background-color: #198754; color: white;">OK</span>'
        )
    status_estoque.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = [
        'substance', 'lote', 'validade', 'quantidade_recebida', 
        'quantidade_disponivel_display', 'fornecedor', 'status_validade'
    ]
    list_filter = ['validade', 'fornecedor', 'refrigerado', 'created_at']
    search_fields = ['lote', 'substance__nome_comum', 'fornecedor']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'validade'
    
    fieldsets = (
        ('Informações do Lote', {
            'fields': ('substance', 'lote', 'validade', 'quantidade_recebida')
        }),
        ('Fornecedor', {
            'fields': ('fornecedor', 'nota_fiscal_ref', 'preco_unitario')
        }),
        ('Armazenamento', {
            'fields': ('local_armazenamento', 'refrigerado')
        }),
        ('Datas', {
            'fields': ('data_fabricacao',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def quantidade_disponivel_display(self, obj):
        qtd = obj.quantidade_disponivel
        if qtd == 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">0</span>'
            )
        return qtd
    quantidade_disponivel_display.short_description = 'Disponível'
    
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
    status_validade.short_description = 'Validade'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['substance', 'batch', 'quantity_on_hand', 'last_updated']
    list_filter = ['substance', 'last_updated']
    search_fields = ['substance__nome_comum', 'batch__lote']
    readonly_fields = ['last_updated']
    
    def has_add_permission(self, request):
        # Inventário é criado automaticamente via StockMovement
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'data_hora', 'tipo', 'substance', 'batch', 'quantidade', 
        'user', 'paciente_nome_display'
    ]
    list_filter = ['tipo', 'data_hora', 'substance']
    search_fields = [
        'substance__nome_comum', 'batch__lote', 'paciente_nome', 
        'paciente_id', 'user__nome'
    ]
    readonly_fields = ['data_hora', 'ip_address', 'user_agent']
    date_hierarchy = 'data_hora'
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('tipo', 'substance', 'batch', 'quantidade', 'user')
        }),
        ('Paciente (para saídas)', {
            'fields': ('paciente_id', 'paciente_nome', 'procedimento', 'registro_clinico_ref'),
            'classes': ('collapse',)
        }),
        ('Documentos e Observações', {
            'fields': ('documento_ref', 'motivo'),
            'classes': ('collapse',)
        }),
        ('Correção', {
            'fields': ('registro_origem',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('data_hora', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def paciente_nome_display(self, obj):
        if obj.paciente_nome:
            return f"{obj.paciente_id} - {obj.paciente_nome}"
        return "-"
    paciente_nome_display.short_description = 'Paciente'
    
    def has_delete_permission(self, request, obj=None):
        # Movimentações não podem ser deletadas (log imutável)
        return False


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['id_interno', 'nome', 'data_nascimento', 'created_at']
    search_fields = ['id_interno', 'nome']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id_interno', 'nome', 'data_nascimento', 'contato')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Customização do Admin Site
admin.site.site_header = "Farmácia Estoque - Administração"
admin.site.site_title = "Farmácia Estoque"
admin.site.index_title = "Painel Administrativo"
