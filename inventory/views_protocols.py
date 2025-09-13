from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Count, Sum
from .models import ProtocolTemplate, ProtocolSubstance, Substance, PatientSession
from .forms_protocols import ProtocolTemplateForm, ProtocolSubstanceFormSet


@login_required
def protocols_list_view(request):
    """View para listar todos os protocolos."""
    protocols = ProtocolTemplate.objects.all().annotate(
        substances_count=Count('substances')
    ).order_by('name')
    
    context = {
        'protocols': protocols,
    }
    return render(request, 'inventory/protocols_list.html', context)


@login_required
def protocol_detail_view(request, protocol_id):
    """View para detalhes de um protocolo."""
    protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    substances = ProtocolSubstance.objects.filter(protocol=protocol).select_related('substance').order_by('order')
    
    # Estatísticas de uso
    sessions_using_protocol = PatientSession.objects.filter(
        protocol_name__icontains=protocol.name
    ).count()
    
    context = {
        'protocol': protocol,
        'substances': substances,
        'sessions_count': sessions_using_protocol,
    }
    return render(request, 'inventory/protocol_detail.html', context)


@login_required
def create_protocol_view(request):
    """View para criar novo protocolo."""
    if request.method == 'POST':
        form = ProtocolTemplateForm(request.POST)
        formset = ProtocolSubstanceFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Criar protocolo
                protocol = form.save(commit=False)
                protocol.created_by = request.user
                protocol.save()
                
                # Processar substâncias do protocolo
                for substance_form in formset:
                    if substance_form.cleaned_data and not substance_form.cleaned_data.get('DELETE', False):
                        substance_data = substance_form.cleaned_data
                        ProtocolSubstance.objects.create(
                            protocol=protocol,
                            substance=substance_data['substance'],
                            default_quantity=substance_data['default_quantity'],
                            is_optional=substance_data.get('is_optional', False),
                            order=substance_data.get('order', 0),
                            notes=substance_data.get('notes', '')
                        )
                
                messages.success(request, f'Protocolo "{protocol.name}" criado com sucesso!')
                return redirect('inventory:protocol_detail', protocol_id=protocol.id)
    else:
        form = ProtocolTemplateForm()
        formset = ProtocolSubstanceFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'action': 'Criar',
    }
    return render(request, 'inventory/protocol_form.html', context)


@login_required
def edit_protocol_view(request, protocol_id):
    """View para editar protocolo existente."""
    protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    
    if request.method == 'POST':
        form = ProtocolTemplateForm(request.POST, instance=protocol)
        formset = ProtocolSubstanceFormSet(request.POST, instance=protocol)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Atualizar protocolo
                protocol = form.save()
                
                # Atualizar substâncias
                formset.save()
                
                messages.success(request, f'Protocolo "{protocol.name}" atualizado com sucesso!')
                return redirect('inventory:protocol_detail', protocol_id=protocol.id)
    else:
        form = ProtocolTemplateForm(instance=protocol)
        formset = ProtocolSubstanceFormSet(instance=protocol)
    
    context = {
        'form': form,
        'formset': formset,
        'protocol': protocol,
        'action': 'Editar',
    }
    return render(request, 'inventory/protocol_form.html', context)


@login_required
def toggle_protocol_status(request, protocol_id):
    """View para ativar/desativar protocolo."""
    protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    
    if request.method == 'POST':
        protocol.is_active = not protocol.is_active
        protocol.save()
        
        status = 'ativado' if protocol.is_active else 'desativado'
        messages.success(request, f'Protocolo "{protocol.name}" {status} com sucesso!')
    
    return redirect('inventory:protocol_detail', protocol_id=protocol.id)


@login_required
def duplicate_protocol_view(request, protocol_id):
    """View para duplicar protocolo existente."""
    original_protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    
    if request.method == 'POST':
        new_name = request.POST.get('new_name')
        if not new_name:
            messages.error(request, 'Nome do novo protocolo é obrigatório.')
            return redirect('inventory:protocol_detail', protocol_id=protocol_id)
        
        with transaction.atomic():
            # Criar novo protocolo
            new_protocol = ProtocolTemplate.objects.create(
                name=new_name,
                description=original_protocol.description,
                default_sessions=original_protocol.default_sessions,
                created_by=request.user
            )
            
            # Copiar substâncias
            original_substances = ProtocolSubstance.objects.filter(protocol=original_protocol)
            for substance in original_substances:
                ProtocolSubstance.objects.create(
                    protocol=new_protocol,
                    substance=substance.substance,
                    default_quantity=substance.default_quantity,
                    is_optional=substance.is_optional,
                    order=substance.order,
                    notes=substance.notes
                )
            
            messages.success(request, f'Protocolo duplicado como "{new_name}" com sucesso!')
            return redirect('inventory:protocol_detail', protocol_id=new_protocol.id)
    
    context = {
        'protocol': original_protocol,
    }
    return render(request, 'inventory/duplicate_protocol.html', context)


@login_required
def protocol_usage_report_view(request):
    """View para relatório de uso de protocolos."""
    # Protocolos mais utilizados
    protocol_usage = {}
    sessions = PatientSession.objects.exclude(protocol_name='').values('protocol_name').annotate(
        count=Count('id'),
        total_value=Sum('total_value')
    ).order_by('-count')
    
    for session_data in sessions:
        protocol_name = session_data['protocol_name']
        # Tentar encontrar protocolo template correspondente
        template = ProtocolTemplate.objects.filter(name__icontains=protocol_name).first()
        
        protocol_usage[protocol_name] = {
            'template': template,
            'sessions_count': session_data['count'],
            'total_value': session_data['total_value'] or 0,
        }
    
    # Protocolos templates não utilizados
    used_names = [name.lower() for name in protocol_usage.keys()]
    unused_protocols = ProtocolTemplate.objects.exclude(
        name__iregex=r'(' + '|'.join(used_names) + ')'
    ) if used_names else ProtocolTemplate.objects.all()
    
    context = {
        'protocol_usage': protocol_usage,
        'unused_protocols': unused_protocols,
    }
    return render(request, 'inventory/protocol_usage_report.html', context)


@login_required
def create_session_from_protocol_view(request, protocol_id, patient_id):
    """View para criar sessão baseada em protocolo."""
    protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Redirecionar para criação de sessão com protocolo pré-selecionado
    return redirect(f'/inventory/pacientes/{patient_id}/nova-sessao/?protocol={protocol_id}')


@login_required
def get_protocol_substances_api(request, protocol_id):
    """API para buscar substâncias de um protocolo (para AJAX)."""
    protocol = get_object_or_404(ProtocolTemplate, id=protocol_id)
    substances = ProtocolSubstance.objects.filter(protocol=protocol).select_related('substance').order_by('order')
    
    data = {
        'protocol': {
            'id': str(protocol.id),
            'name': protocol.name,
            'description': protocol.description,
            'default_sessions': protocol.default_sessions,
        },
        'substances': []
    }
    
    for ps in substances:
        data['substances'].append({
            'id': str(ps.id),
            'substance_id': str(ps.substance.id),
            'substance_name': ps.substance.nome_comum,
            'default_quantity': float(ps.default_quantity),
            'unit_price': float(ps.substance.preco_padrao),
            'is_optional': ps.is_optional,
            'order': ps.order,
            'notes': ps.notes,
        })
    
    return JsonResponse(data)


@login_required
def quick_protocol_stats_api(request):
    """API para estatísticas rápidas de protocolos."""
    total_protocols = ProtocolTemplate.objects.count()
    active_protocols = ProtocolTemplate.objects.filter(is_active=True).count()
    
    # Protocolo mais usado (aproximação)
    most_used = None
    sessions_with_protocol = PatientSession.objects.exclude(protocol_name='').values('protocol_name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    if sessions_with_protocol:
        most_used = sessions_with_protocol['protocol_name']
    
    data = {
        'total_protocols': total_protocols,
        'active_protocols': active_protocols,
        'inactive_protocols': total_protocols - active_protocols,
        'most_used_protocol': most_used,
    }
    
    return JsonResponse(data)

