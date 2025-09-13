from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Max
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from .models import Patient, PatientSession, Substance, Unit, StockMovement, ResponsibilityTerm
import csv
from io import StringIO

User = get_user_model()

@login_required
def patients_report_view(request):
    """
    Relatório completo de pacientes com filtros avançados.
    """
    # Parâmetros de filtro
    professional_filter = request.GET.get('professional', '')
    unit_filter = request.GET.get('unit', '')
    substance_filter = request.GET.get('substance', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status_filter = request.GET.get('status', 'active')  # active, inactive, all
    
    # Query base
    patients = Patient.objects.all()
    
    # Aplicar filtros
    if status_filter == 'active':
        patients = patients.filter(ativo=True)
    elif status_filter == 'inactive':
        patients = patients.filter(ativo=False)
    
    if unit_filter:
        patients = patients.filter(unidade_principal_id=unit_filter)
    
    # Filtros baseados em sessões
    session_filters = Q()
    
    if professional_filter:
        session_filters &= Q(sessoes__aplicado_por_id=professional_filter)
    
    if substance_filter:
        session_filters &= Q(sessoes__substancias_utilizadas__substance_id=substance_filter)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            session_filters &= Q(sessoes__data_sessao__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            session_filters &= Q(sessoes__data_sessao__lte=date_to_obj)
        except ValueError:
            pass
    
    if session_filters:
        patients = patients.filter(session_filters).distinct()
    
    # Adicionar estatísticas para cada paciente
    patients_with_stats = []
    for patient in patients.select_related('unidade_principal'):
        # Última sessão
        last_session = PatientSession.objects.filter(
            patient=patient
        ).order_by('-data_sessao').first()
        
        # Total de sessões
        total_sessions = PatientSession.objects.filter(patient=patient).count()
        
        # Profissionais que atenderam
        professionals = PatientSession.objects.filter(
            patient=patient
        ).values_list('aplicado_por__username', flat=True).distinct()
        
        # Substâncias utilizadas
        substances_used = PatientSession.objects.filter(
            patient=patient
        ).values_list(
            'substancias_utilizadas__substance__nome_comum', 
            flat=True
        ).distinct()
        
        patients_with_stats.append({
            'patient': patient,
            'last_session': last_session,
            'total_sessions': total_sessions,
            'professionals': list(professionals),
            'substances_used': list(substances_used),
        })
    
    # Dados para filtros
    professionals = User.objects.filter(
        is_active=True
    ).order_by('username')
    
    units = Unit.objects.filter(ativo=True).order_by('nome')
    
    substances = Substance.objects.all().order_by('nome_comum')
    
    # Estatísticas gerais
    total_patients = len(patients_with_stats)
    active_patients = sum(1 for p in patients_with_stats if p['patient'].ativo)
    
    # Estatísticas por profissional
    professional_stats = {}
    for patient_data in patients_with_stats:
        for prof in patient_data['professionals']:
            if prof not in professional_stats:
                professional_stats[prof] = {
                    'patients': set(),
                    'sessions': 0
                }
            professional_stats[prof]['patients'].add(patient_data['patient'].id)
    
    # Converter sets para contagem
    for prof in professional_stats:
        professional_stats[prof]['patients'] = len(professional_stats[prof]['patients'])
    
    context = {
        'patients_with_stats': patients_with_stats,
        'professionals': professionals,
        'units': units,
        'substances': substances,
        'total_patients': total_patients,
        'active_patients': active_patients,
        'professional_stats': professional_stats,
        
        # Filtros aplicados
        'filters': {
            'professional': professional_filter,
            'unit': unit_filter,
            'substance': substance_filter,
            'date_from': date_from,
            'date_to': date_to,
            'status': status_filter,
        }
    }
    
    return render(request, 'inventory/patients_report.html', context)

@login_required
def professional_stats_view(request):
    """
    Estatísticas detalhadas por profissional.
    """
    professional_id = request.GET.get('professional_id')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if not professional_id:
        return JsonResponse({'error': 'Professional ID required'}, status=400)
    
    professional = get_object_or_404(User, id=professional_id)
    
    # Filtros de data
    date_filters = Q()
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_filters &= Q(data_sessao__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            date_filters &= Q(data_sessao__lte=date_to_obj)
        except ValueError:
            pass
    
    # Sessões do profissional
    sessions = PatientSession.objects.filter(
        aplicado_por=professional
    ).filter(date_filters)
    
    # Estatísticas
    total_sessions = sessions.count()
    unique_patients = sessions.values('patient').distinct().count()
    
    # Substâncias mais utilizadas
    top_substances = sessions.values(
        'substancias_utilizadas__substance__nome_comum'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Sessões por mês
    monthly_sessions = sessions.extra(
        select={'month': "DATE_FORMAT(data_sessao, '%%Y-%%m')"}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Pacientes atendidos
    patients_attended = sessions.values(
        'patient__nome',
        'patient__codigo',
        'patient__unidade_principal__nome'
    ).annotate(
        session_count=Count('id'),
        last_session=Max('data_sessao')
    ).order_by('-session_count')
    
    data = {
        'professional': {
            'id': professional.id,
            'name': professional.username,
            'full_name': getattr(professional, 'nome', professional.username)
        },
        'stats': {
            'total_sessions': total_sessions,
            'unique_patients': unique_patients,
            'avg_sessions_per_patient': round(total_sessions / unique_patients, 2) if unique_patients > 0 else 0
        },
        'top_substances': list(top_substances),
        'monthly_sessions': list(monthly_sessions),
        'patients_attended': list(patients_attended)
    }
    
    return JsonResponse(data)

@login_required
def export_patients_csv(request):
    """
    Exportar relatório de pacientes para CSV.
    """
    # Aplicar os mesmos filtros da view principal
    professional_filter = request.GET.get('professional', '')
    unit_filter = request.GET.get('unit', '')
    substance_filter = request.GET.get('substance', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status_filter = request.GET.get('status', 'active')
    
    # Reutilizar lógica de filtros (simplificada)
    patients = Patient.objects.all()
    
    if status_filter == 'active':
        patients = patients.filter(ativo=True)
    elif status_filter == 'inactive':
        patients = patients.filter(ativo=False)
    
    if unit_filter:
        patients = patients.filter(unidade_principal_id=unit_filter)
    
    # Criar CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow([
        'Código',
        'Nome',
        'Unidade',
        'Status',
        'Total Sessões',
        'Última Sessão',
        'Profissionais',
        'Substâncias Utilizadas'
    ])
    
    # Dados
    for patient in patients.select_related('unidade_principal'):
        last_session = PatientSession.objects.filter(
            patient=patient
        ).order_by('-data_sessao').first()
        
        total_sessions = PatientSession.objects.filter(patient=patient).count()
        
        professionals = ', '.join(
            PatientSession.objects.filter(
                patient=patient
            ).values_list('aplicado_por__username', flat=True).distinct()
        )
        
        substances = ', '.join(
            PatientSession.objects.filter(
                patient=patient
            ).values_list(
                'substancias_utilizadas__substance__nome_comum', 
                flat=True
            ).distinct()
        )
        
        writer.writerow([
            patient.codigo,
            patient.nome,
            patient.unidade_principal.nome if patient.unidade_principal else '',
            'Ativo' if patient.ativo else 'Inativo',
            total_sessions,
            last_session.data_sessao.strftime('%d/%m/%Y') if last_session else '',
            professionals,
            substances
        ])
    
    # Resposta HTTP
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="relatorio_pacientes_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
    
    return response

