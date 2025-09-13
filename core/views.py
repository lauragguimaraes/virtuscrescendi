from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from inventory.models import (
    Substance, Batch, Inventory, StockMovement, Unit, 
    TransferNew, Patient, PatientSession
)


@login_required
def dashboard_view(request):
    """Dashboard principal reformulado com estatísticas avançadas."""
    user = request.user
    
    # Estatísticas gerais
    total_substances = Substance.objects.count()
    total_batches = Batch.objects.count()
    
    # Estoque atual total
    total_stock = Inventory.objects.aggregate(
        total=Sum('quantity_on_hand')
    )['total'] or 0
    
    # Estatísticas por unidade
    try:
        rp_unit = Unit.objects.get(codigo='RP')
        bauru_unit = Unit.objects.get(codigo='BR')
        
        # Estatísticas Ribeirão Preto
        rp_stock = Inventory.objects.filter(unit=rp_unit).aggregate(
            total=Sum('quantity_on_hand')
        )['total'] or 0
        
        rp_substances = Inventory.objects.filter(
            unit=rp_unit, 
            quantity_on_hand__gt=0
        ).values('substance').distinct().count()
        
        rp_alerts = Inventory.objects.filter(
            unit=rp_unit,
            quantity_on_hand__lt=F('substance__estoque_minimo_default')
        ).count()
        
        # Estatísticas Bauru
        bauru_stock = Inventory.objects.filter(unit=bauru_unit).aggregate(
            total=Sum('quantity_on_hand')
        )['total'] or 0
        
        bauru_substances = Inventory.objects.filter(
            unit=bauru_unit, 
            quantity_on_hand__gt=0
        ).values('substance').distinct().count()
        
        bauru_alerts = Inventory.objects.filter(
            unit=bauru_unit,
            quantity_on_hand__lt=F('substance__estoque_minimo_default')
        ).count()
        
    except Unit.DoesNotExist:
        # Fallback se as unidades não existirem
        rp_stock = bauru_stock = 0
        rp_substances = bauru_substances = 0
        rp_alerts = bauru_alerts = 0
    
    # NOVAS FUNCIONALIDADES DO DASHBOARD REFORMULADO
    
    # 1. Transferências Recentes (últimos 7 dias)
    data_inicio_semana = timezone.now() - timedelta(days=7)
    recent_transfers = TransferNew.objects.filter(
        data_criacao__gte=data_inicio_semana
    ).select_related(
        'unidade_origem', 'unidade_destino', 'criado_por'
    ).prefetch_related('itens').order_by('-data_criacao')[:5]
    
    # Total de transferências hoje
    transfers_today = TransferNew.objects.filter(
        data_criacao__date=timezone.now().date()
    ).count()
    
    # 2. Top 10 Substâncias Mais Utilizadas (últimos 30 dias)
    data_inicio_mes = timezone.now() - timedelta(days=30)
    top_substances = StockMovement.objects.filter(
        data_hora__gte=data_inicio_mes,
        tipo='saida'
    ).values(
        'substance__nome_comum'
    ).annotate(
        total_usado=Sum('quantidade'),
        vezes_usado=Count('id')
    ).order_by('-total_usado')[:10]
    
    # 3. Pacientes Ativos por Unidade (últimos 30 dias)
    active_patients_rp = Patient.objects.filter(
        unidade_principal=rp_unit,
        ativo=True
    ).count() if 'rp_unit' in locals() else 0
    
    active_patients_bauru = Patient.objects.filter(
        unidade_principal=bauru_unit,
        ativo=True
    ).count() if 'bauru_unit' in locals() else 0
    
    # 4. Sessões Hoje
    sessions_today = PatientSession.objects.filter(
        data_sessao=timezone.now().date()
    ).count()
    
    # 5. Consumo Semanal (últimos 7 dias)
    weekly_consumption = StockMovement.objects.filter(
        data_hora__gte=data_inicio_semana,
        tipo='saida'
    ).aggregate(
        total=Sum('quantidade')
    )['total'] or 0
    
    # 6. Alertas Críticos Melhorados
    critical_alerts = {
        'low_stock': 0,
        'expiring_soon': 0,
        'expired': 0,
        'zero_stock': 0
    }
    
    # Substâncias com estoque baixo
    low_stock_substances = []
    for substance in Substance.objects.all():
        if substance.estoque_baixo:
            low_stock_substances.append(substance)
            critical_alerts['low_stock'] += 1
    
    # Lotes vencendo em 30 dias
    data_limite = timezone.now().date() + timedelta(days=30)
    expiring_batches = Batch.objects.filter(
        validade__lte=data_limite,
        validade__gte=timezone.now().date()
    ).count()
    critical_alerts['expiring_soon'] = expiring_batches
    
    # Lotes vencidos
    expired_batches = Batch.objects.filter(
        validade__lt=timezone.now().date()
    ).count()
    critical_alerts['expired'] = expired_batches
    
    # Substâncias com estoque zero
    zero_stock = Inventory.objects.filter(
        quantity_on_hand=0
    ).count()
    critical_alerts['zero_stock'] = zero_stock
    
    # 7. Movimentações Recentes Melhoradas
    recent_movements = StockMovement.objects.filter(
        data_hora__gte=data_inicio_semana
    ).select_related(
        'substance', 'batch', 'user', 'unit', 'paciente'
    ).order_by('-data_hora')[:8]
    
    # 8. Estatísticas de Crescimento
    # Comparar com semana anterior
    data_semana_anterior = timezone.now() - timedelta(days=14)
    
    movements_this_week = StockMovement.objects.filter(
        data_hora__gte=data_inicio_semana
    ).count()
    
    movements_last_week = StockMovement.objects.filter(
        data_hora__gte=data_semana_anterior,
        data_hora__lt=data_inicio_semana
    ).count()
    
    # Calcular crescimento percentual
    if movements_last_week > 0:
        movement_growth = ((movements_this_week - movements_last_week) / movements_last_week) * 100
    else:
        movement_growth = 100 if movements_this_week > 0 else 0
    
    context = {
        # Estatísticas básicas
        'total_substances': total_substances,
        'total_batches': total_batches,
        'total_stock': total_stock,
        
        # Estatísticas por unidade
        'rp_stats': {
            'substances': rp_substances,
            'stock': rp_stock,
            'alerts': rp_alerts,
            'active_patients': active_patients_rp,
        },
        'bauru_stats': {
            'substances': bauru_substances,
            'stock': bauru_stock,
            'alerts': bauru_alerts,
            'active_patients': active_patients_bauru,
        },
        
        # NOVAS SEÇÕES DO DASHBOARD REFORMULADO
        'recent_transfers': recent_transfers,
        'transfers_today': transfers_today,
        'top_substances': top_substances,
        'sessions_today': sessions_today,
        'weekly_consumption': weekly_consumption,
        'critical_alerts': critical_alerts,
        'recent_movements': recent_movements,
        'movement_growth': round(movement_growth, 1),
        
        # Dados para gráficos
        'chart_data': {
            'rp_stock': float(rp_stock),
            'bauru_stock': float(bauru_stock),
            'total_patients': active_patients_rp + active_patients_bauru,
            'total_alerts': critical_alerts['low_stock'] + critical_alerts['expiring_soon'],
        }
    }
    
    return render(request, 'core/dashboard_new.html', context)


@login_required
def alerts_view(request):
    """View para mostrar todos os alertas do sistema."""
    # Substâncias com estoque baixo
    low_stock_substances = []
    for substance in Substance.objects.all():
        if substance.estoque_baixo:
            low_stock_substances.append({
                'substance': substance,
                'current_stock': substance.get_estoque_total(),
                'minimum_stock': substance.estoque_minimo
            })
    
    # Lotes vencendo
    data_limite_30 = timezone.now().date() + timedelta(days=30)
    data_limite_60 = timezone.now().date() + timedelta(days=60)
    data_limite_90 = timezone.now().date() + timedelta(days=90)
    
    expiring_30_days = Batch.objects.filter(
        validade__lte=data_limite_30,
        validade__gt=timezone.now().date()
    ).select_related('substance', 'unit').order_by('validade')
    
    expiring_60_days = Batch.objects.filter(
        validade__lte=data_limite_60,
        validade__gt=data_limite_30
    ).select_related('substance', 'unit').order_by('validade')
    
    expiring_90_days = Batch.objects.filter(
        validade__lte=data_limite_90,
        validade__gt=data_limite_60
    ).select_related('substance', 'unit').order_by('validade')
    
    # Lotes vencidos
    expired_batches = Batch.objects.filter(
        validade__lt=timezone.now().date()
    ).select_related('substance', 'unit').order_by('validade')
    
    context = {
        'low_stock_substances': low_stock_substances,
        'expiring_30_days': expiring_30_days,
        'expiring_60_days': expiring_60_days,
        'expiring_90_days': expiring_90_days,
        'expired_batches': expired_batches,
    }
    
    return render(request, 'core/alerts.html', context)

