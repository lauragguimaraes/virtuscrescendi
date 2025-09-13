from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from .models import (
    Patient, PatientSession, SessionSubstance, 
    Substance, Batch, Inventory, StockMovement,
    ProtocolTemplate, ProtocolSubstance, Unit
)
from .forms import PatientSessionForm, SessionSubstanceFormSet


@login_required
def patient_sessions_view(request, patient_id=None):
    """View para listar sessões de pacientes."""
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        sessions = PatientSession.objects.filter(patient=patient).order_by('-session_date', '-session_number')
        context = {
            'patient': patient,
            'sessions': sessions,
        }
        return render(request, 'inventory/patient_sessions.html', context)
    else:
        # Listar todos os pacientes com suas últimas sessões
        patients = Patient.objects.filter(ativo=True).prefetch_related('sessions')
        context = {
            'patients': patients,
        }
        return render(request, 'inventory/patients_list.html', context)


@login_required
def create_session_view(request, patient_id):
    """View para criar nova sessão de paciente."""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Determinar próximo número de sessão
    last_session = PatientSession.objects.filter(patient=patient).order_by('-session_number').first()
    next_session_number = (last_session.session_number + 1) if last_session else 1
    
    if request.method == 'POST':
        form = PatientSessionForm(request.POST)
        formset = SessionSubstanceFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Criar sessão
                session = form.save(commit=False)
                session.patient = patient
                session.session_number = next_session_number
                session.unit = patient.unidade_principal
                session.created_by = request.user
                session.save()
                
                total_value = Decimal('0')
                
                # Processar substâncias da sessão
                for substance_form in formset:
                    if substance_form.cleaned_data and not substance_form.cleaned_data.get('DELETE', False):
                        substance_data = substance_form.cleaned_data
                        substance = substance_data['substance']
                        quantity = substance_data['quantity']
                        unit_price = substance_data.get('unit_price') or substance.preco_padrao
                        
                        # Criar registro da substância na sessão
                        session_substance = SessionSubstance.objects.create(
                            session=session,
                            substance=substance,
                            quantity=quantity,
                            unit_price=unit_price,
                            notes=substance_data.get('notes', ''),
                            created_by=request.user
                        )
                        
                        total_value += session_substance.total_price
                        
                        # Processar saída de estoque (FIFO)
                        remaining_quantity = quantity
                        inventories = Inventory.objects.filter(
                            substance=substance,
                            unit=session.unit,
                            quantity_on_hand__gt=0
                        ).select_related('batch').order_by('batch__validade', 'batch__created_at')
                        
                        for inventory in inventories:
                            if remaining_quantity <= 0:
                                break
                            
                            # Quantidade a retirar deste lote
                            quantity_to_take = min(remaining_quantity, inventory.quantity_on_hand)
                            
                            # Criar movimentação de estoque
                            StockMovement.objects.create(
                                substance=substance,
                                batch=inventory.batch,
                                unit=session.unit,
                                tipo='saida',
                                quantidade=quantity_to_take,
                                motivo=f'Sessão {session.session_number} - {patient.nome}',
                                paciente=patient,
                                paciente_nome=patient.nome,
                                procedimento=session.procedure_description,
                                session=session,
                                user=request.user,
                                ip_address=request.META.get('REMOTE_ADDR'),
                                user_agent=request.META.get('HTTP_USER_AGENT', '')
                            )
                            
                            # Atualizar estoque
                            inventory.quantity_on_hand -= quantity_to_take
                            inventory.save()
                            
                            remaining_quantity -= quantity_to_take
                        
                        if remaining_quantity > 0:
                            messages.warning(
                                request, 
                                f'Estoque insuficiente para {substance.nome_comum}. '
                                f'Faltaram {remaining_quantity} unidades.'
                            )
                
                # Atualizar valor total da sessão
                session.total_value = total_value
                session.save()
                
                messages.success(request, f'Sessão {session.session_number} criada com sucesso!')
                return redirect('inventory:patient_sessions', patient_id=patient.id)
    else:
        form = PatientSessionForm(initial={
            'session_date': timezone.now().date(),
        })
        formset = SessionSubstanceFormSet()
    
    # Buscar protocolos disponíveis
    protocols = ProtocolTemplate.objects.filter(is_active=True)
    
    context = {
        'patient': patient,
        'form': form,
        'formset': formset,
        'next_session_number': next_session_number,
        'protocols': protocols,
    }
    return render(request, 'inventory/create_session.html', context)


@login_required
def session_detail_view(request, session_id):
    """View para detalhes de uma sessão."""
    session = get_object_or_404(PatientSession, id=session_id)
    substances = SessionSubstance.objects.filter(session=session).select_related('substance')
    movements = StockMovement.objects.filter(session=session).select_related('substance', 'batch')
    
    context = {
        'session': session,
        'substances': substances,
        'movements': movements,
    }
    return render(request, 'inventory/session_detail.html', context)


@login_required
def update_payment_view(request, session_id):
    """View para atualizar pagamento de uma sessão."""
    session = get_object_or_404(PatientSession, id=session_id)
    
    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        payment_method = request.POST.get('payment_method')
        payment_notes = request.POST.get('payment_notes', '')
        
        session.payment_status = payment_status
        session.payment_method = payment_method
        session.payment_notes = payment_notes
        
        if payment_status == 'pago':
            session.payment_date = timezone.now().date()
        
        session.save()
        
        messages.success(request, 'Pagamento atualizado com sucesso!')
        return redirect('inventory:session_detail', session_id=session.id)
    
    context = {
        'session': session,
    }
    return render(request, 'inventory/update_payment.html', context)


@login_required
def financial_reports_view(request):
    """View para relatórios financeiros."""
    # Filtros
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    unit_id = request.GET.get('unit')
    payment_status = request.GET.get('payment_status')
    
    # Query base
    sessions = PatientSession.objects.all()
    
    # Aplicar filtros
    if start_date:
        sessions = sessions.filter(session_date__gte=start_date)
    if end_date:
        sessions = sessions.filter(session_date__lte=end_date)
    if unit_id:
        sessions = sessions.filter(unit_id=unit_id)
    if payment_status:
        sessions = sessions.filter(payment_status=payment_status)
    
    # Estatísticas
    total_sessions = sessions.count()
    total_revenue = sessions.aggregate(total=Sum('total_value'))['total'] or Decimal('0')
    paid_revenue = sessions.filter(payment_status='pago').aggregate(total=Sum('total_value'))['total'] or Decimal('0')
    pending_revenue = sessions.filter(payment_status='pendente').aggregate(total=Sum('total_value'))['total'] or Decimal('0')
    
    # Sessões por status de pagamento
    payment_stats = sessions.values('payment_status').annotate(
        count=Count('id'),
        total_value=Sum('total_value')
    ).order_by('payment_status')
    
    # Receita por unidade
    unit_stats = sessions.values('unit__nome').annotate(
        count=Count('id'),
        total_value=Sum('total_value')
    ).order_by('-total_value')
    
    # Substâncias mais utilizadas
    substance_stats = SessionSubstance.objects.filter(
        session__in=sessions
    ).values('substance__nome_comum').annotate(
        quantity_used=Sum('quantity'),
        total_revenue=Sum('total_price'),
        sessions_count=Count('session', distinct=True)
    ).order_by('-quantity_used')[:10]
    
    context = {
        'sessions': sessions.order_by('-session_date')[:50],  # Últimas 50 sessões
        'total_sessions': total_sessions,
        'total_revenue': total_revenue,
        'paid_revenue': paid_revenue,
        'pending_revenue': pending_revenue,
        'payment_stats': payment_stats,
        'unit_stats': unit_stats,
        'substance_stats': substance_stats,
        'units': Unit.objects.filter(ativo=True),
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'unit_id': unit_id,
            'payment_status': payment_status,
        }
    }
    return render(request, 'inventory/financial_reports.html', context)


@login_required
def get_protocol_substances(request, protocol_id):
    """API para buscar substâncias de um protocolo."""
    protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    substances = ProtocolSubstance.objects.filter(protocol=protocol).select_related('substance')
    
    data = []
    for ps in substances:
        data.append({
            'substance_id': str(ps.substance.id),
            'substance_name': ps.substance.nome_comum,
            'default_quantity': float(ps.default_quantity),
            'unit_price': float(ps.substance.preco_padrao),
            'is_optional': ps.is_optional,
            'notes': ps.notes,
        })
    
    return JsonResponse({'substances': data})


@login_required
def substance_prices_view(request):
    """View para gerenciar preços das substâncias."""
    if request.method == 'POST':
        substance_id = request.POST.get('substance_id')
        new_price = request.POST.get('price')
        
        try:
            substance = Substance.objects.get(id=substance_id)
            substance.preco_padrao = Decimal(new_price)
            substance.save()
            
            messages.success(request, f'Preço de {substance.nome_comum} atualizado para R$ {new_price}')
        except (Substance.DoesNotExist, ValueError):
            messages.error(request, 'Erro ao atualizar preço')
        
        return redirect('inventory:substance_prices')
    
    substances = Substance.objects.all().order_by('nome_comum')
    
    context = {
        'substances': substances,
    }
    return render(request, 'inventory/substance_prices.html', context)

