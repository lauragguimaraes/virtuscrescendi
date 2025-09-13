from django.urls import path
from . import views, views_protocols, views_transfers, views_reports
from .views_sessions_simple import (
    patient_sessions_view, patient_edit_view, substance_prices_view, financial_reports_view,
    create_session_view, session_detail_view, update_payment_view, get_protocol_substances
)

app_name = 'inventory'

urlpatterns = [
    # Entrada de estoque
    path('entrada/', views.stock_entry_view, name='stock_entry'),
    
    # Saída de estoque
    path('saida/', views.stock_exit_view, name='stock_exit'),
    
    # Movimentações
    path('movimentacoes/', views.stock_movements_view, name='stock_movements'),
    
    # API endpoints
    path('api/substance-stock/', views.get_substance_stock, name='api_substance_stock'),
    
    # URLs para gestão de pacientes e sessões (versão simples)
    path('pacientes/', patient_sessions_view, name='patients_list'),
    path('pacientes/<uuid:patient_id>/editar/', patient_edit_view, name='patient_edit'),
    path('pacientes/<uuid:patient_id>/', patient_sessions_view, name='patient_sessions'),
    path('pacientes/<uuid:patient_id>/nova-sessao/', create_session_view, name='create_session'),
    path('sessoes/<uuid:session_id>/', session_detail_view, name='session_detail'),
    path('sessoes/<uuid:session_id>/pagamento/', update_payment_view, name='update_payment'),
    
    # URLs para controle financeiro (versão simples)
    path('precos/', substance_prices_view, name='substance_prices'),
    path('relatorios/financeiro/', financial_reports_view, name='financial_reports'),
    
    # URLs para protocolos clínicos
    path('protocolos/', views_protocols.protocols_list_view, name='protocols_list'),
    path('protocolos/novo/', views_protocols.create_protocol_view, name='create_protocol'),
    path('protocolos/<uuid:protocol_id>/', views_protocols.protocol_detail_view, name='protocol_detail'),
    path('protocolos/<uuid:protocol_id>/editar/', views_protocols.edit_protocol_view, name='edit_protocol'),
    path('protocolos/<uuid:protocol_id>/toggle/', views_protocols.toggle_protocol_status, name='toggle_protocol'),
    path('protocolos/<uuid:protocol_id>/duplicar/', views_protocols.duplicate_protocol_view, name='duplicate_protocol'),
    path('protocolos/<uuid:protocol_id>/paciente/<uuid:patient_id>/sessao/', views_protocols.create_session_from_protocol_view, name='create_session_from_protocol'),
    path('relatorios/protocolos/', views_protocols.protocol_usage_report_view, name='protocol_usage_report'),
    
    # APIs
    path('api/protocolo/<uuid:protocol_id>/substancias/', get_protocol_substances, name='api_protocol_substances'),
    path('api/protocolos/<uuid:protocol_id>/substancias/', views_protocols.get_protocol_substances_api, name='api_protocol_substances_detailed'),
    path('api/protocolos/stats/', views_protocols.quick_protocol_stats_api, name='api_protocol_stats'),
    
    # URLs para transferências entre unidades
    path('transferencias/', views_transfers.transfers_list, name='transfers_list'),
    path('transferencias/nova/', views_transfers.transfer_create, name='transfer_create'),
    path('transferencias/<uuid:transfer_id>/', views_transfers.transfer_detail, name='transfer_detail'),
    path('api/estoque-substancia/', views_transfers.get_substance_stock, name='api_substance_stock_transfer'),
    
    # URLs para relatórios de pacientes
    path('relatorios/pacientes/', views_reports.patients_report_view, name='patients_report'),
    path('relatorios/pacientes/export/', views_reports.export_patients_csv, name='export_patients_csv'),
    path('api/professional-stats/', views_reports.professional_stats_view, name='api_professional_stats'),
]

