from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from inventory.models import Patient, Substance, Unit, StockMovement
from decimal import Decimal

@login_required
def patient_sessions_view(request, patient_id=None):
    """Lista todos os pacientes"""
    patients = Patient.objects.all().order_by('nome')
    
    # Adicionar estatísticas básicas para cada paciente
    for patient in patients:
        # Contar sessões (movimentações únicas por data)
        patient.total_sessions = StockMovement.objects.filter(
            paciente=patient
        ).values('data_hora__date').distinct().count()
        
        # Última sessão
        last_movement = StockMovement.objects.filter(
            paciente=patient
        ).order_by('-data_hora').first()
        
        patient.last_session_date = last_movement.data_hora.date() if last_movement else None
    
    context = {
        'patients': patients,
        'total_patients': patients.count(),
    }
    return render(request, 'inventory/patients_list.html', context)

@login_required
def patient_edit_view(request, patient_id):
    """Editar paciente (apenas admin)"""
    if request.user.role != 'admin':
        messages.error(request, 'Apenas administradores podem editar pacientes.')
        return redirect('inventory:patients_list')
    
    patient = get_object_or_404(Patient, id=patient_id)
    units = Unit.objects.filter(ativo=True)
    
    if request.method == 'POST':
        try:
            # Atualizar dados do paciente
            patient.codigo = request.POST.get('codigo', '').strip()
            patient.nome = request.POST.get('nome', '').strip()
            patient.data_nascimento = request.POST.get('data_nascimento') or None
            patient.telefone = request.POST.get('telefone', '').strip()
            patient.email = request.POST.get('email', '').strip()
            patient.observacoes = request.POST.get('observacoes', '').strip()
            patient.ativo = 'ativo' in request.POST
            
            # Atualizar unidade principal
            unidade_id = request.POST.get('unidade_principal')
            if unidade_id:
                patient.unidade_principal = Unit.objects.get(id=unidade_id)
            
            patient.save()
            
            messages.success(request, f'Paciente {patient.nome} atualizado com sucesso!')
            return redirect('inventory:patients_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar paciente: {str(e)}')
    
    # Adicionar estatísticas
    patient.total_sessions = StockMovement.objects.filter(
        paciente=patient
    ).values('data_hora__date').distinct().count()
    
    last_movement = StockMovement.objects.filter(
        paciente=patient
    ).order_by('-data_hora').first()
    
    patient.last_session_date = last_movement.data_hora.date() if last_movement else None
    
    context = {
        'patient': patient,
        'units': units,
    }
    return render(request, 'inventory/patient_edit.html', context)

@login_required
def substance_prices_view(request):
    """Gestão de preços das substâncias"""
    substances = Substance.objects.all().order_by('nome_comum')
    
    if request.method == 'POST':
        # Atualizar preços
        for substance in substances:
            price_key = f'price_{substance.id}'
            if price_key in request.POST:
                try:
                    new_price = Decimal(request.POST[price_key] or '0')
                    substance.preco_padrao = new_price
                    substance.save()
                except (ValueError, TypeError):
                    pass
        
        messages.success(request, 'Preços atualizados com sucesso!')
        return redirect('inventory:substance_prices')
    
    context = {
        'substances': substances,
        'total_substances': substances.count(),
    }
    return render(request, 'inventory/substance_prices.html', context)

@login_required
def financial_reports_view(request):
    """Relatórios financeiros básicos"""
    # Calcular estatísticas básicas
    total_patients = Patient.objects.filter(ativo=True).count()
    total_sessions = StockMovement.objects.values('paciente', 'data_hora__date').distinct().count()
    
    # Receita estimada (baseada nos preços das substâncias)
    movements = StockMovement.objects.filter(tipo='saida').select_related('substance', 'paciente')
    total_revenue = sum(
        movement.quantidade * (movement.substance.preco_padrao or Decimal('0'))
        for movement in movements
    )
    
    context = {
        'total_patients': total_patients,
        'total_sessions': total_sessions,
        'total_revenue': total_revenue,
        'recent_movements': movements.order_by('-data_hora')[:10],
    }
    return render(request, 'inventory/financial_reports.html', context)

# Views placeholder para funcionalidades em desenvolvimento
@login_required
def create_session_view(request, patient_id):
    """Placeholder para criação de sessão."""
    return JsonResponse({'message': 'Funcionalidade em desenvolvimento'})

@login_required
def session_detail_view(request, session_id):
    """Placeholder para detalhes da sessão."""
    return JsonResponse({'message': 'Funcionalidade em desenvolvimento'})

@login_required
def update_payment_view(request, session_id):
    """Placeholder para atualização de pagamento."""
    return JsonResponse({'message': 'Funcionalidade em desenvolvimento'})

@login_required
def get_protocol_substances(request, protocol_id):
    """Placeholder para API de substâncias do protocolo."""
    return JsonResponse({'message': 'Funcionalidade em desenvolvimento'})

