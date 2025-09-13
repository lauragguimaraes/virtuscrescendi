from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from .models import Substance, Batch, Inventory, StockMovement, Patient
from .forms import StockEntryForm, StockExitForm


@login_required
def stock_entry_view(request):
    """
    View para entrada de estoque (apenas chefes e admins).
    """
    if not (request.user.role in ['chefe', 'admin']):
        messages.error(request, 'Acesso negado. Apenas chefes e administradores podem registrar entradas.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = StockEntryForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Criar lote
                    batch = Batch.objects.create(
                        substance=form.cleaned_data['substance'],
                        lote=form.cleaned_data['lote'],
                        validade=form.cleaned_data['validade'],
                        quantidade_recebida=form.cleaned_data['quantidade'],
                        fornecedor=form.cleaned_data['fornecedor'],
                        nota_fiscal_ref=form.cleaned_data.get('nota_fiscal_ref', ''),
                        preco_unitario=form.cleaned_data.get('preco_unitario', Decimal('0')),
                        created_by=request.user,
                    )
                    
                    # Criar entrada no estoque
                    inventory, created = Inventory.objects.get_or_create(
                        substance=form.cleaned_data['substance'],
                        batch=batch,
                        defaults={'quantity_on_hand': form.cleaned_data['quantidade']}
                    )
                    
                    # Registrar movimentação
                    StockMovement.objects.create(
                        substance=form.cleaned_data['substance'],
                        batch=batch,
                        tipo='entrada',
                        quantidade=form.cleaned_data['quantidade'],
                        motivo=form.cleaned_data.get('motivo', 'Entrada de estoque'),
                        user=request.user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    )
                    
                    messages.success(request, f'Entrada registrada com sucesso! Lote {batch.lote} adicionado.')
                    return redirect('inventory:stock_entry')
                    
            except Exception as e:
                messages.error(request, f'Erro ao registrar entrada: {str(e)}')
    else:
        form = StockEntryForm()
    
    return render(request, 'inventory/stock_entry.html', {'form': form})


@login_required
def stock_exit_view(request):
    """
    View para saída de estoque (todos os usuários autenticados).
    """
    if request.method == 'POST':
        form = StockExitForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    substance = form.cleaned_data['substance']
                    quantidade_solicitada = form.cleaned_data['quantidade']
                    
                    # Buscar lotes disponíveis (FIFO - primeiro a vencer)
                    available_batches = Inventory.objects.filter(
                        substance=substance,
                        quantity_on_hand__gt=0
                    ).select_related('batch').order_by('batch__validade')
                    
                    if not available_batches.exists():
                        messages.error(request, f'Não há estoque disponível para {substance.nome_comum}')
                        return render(request, 'inventory/stock_exit.html', {'form': form})
                    
                    # Verificar se há estoque suficiente
                    total_disponivel = sum(inv.quantity_on_hand for inv in available_batches)
                    if total_disponivel < quantidade_solicitada:
                        messages.error(request, f'Estoque insuficiente. Disponível: {total_disponivel}, Solicitado: {quantidade_solicitada}')
                        return render(request, 'inventory/stock_exit.html', {'form': form})
                    
                    # Processar saída usando FIFO
                    quantidade_restante = quantidade_solicitada
                    movimentacoes_criadas = []
                    
                    for inventory in available_batches:
                        if quantidade_restante <= 0:
                            break
                        
                        # Verificar se o lote está vencido
                        if inventory.batch.vencido:
                            messages.warning(request, f'Atenção: Lote {inventory.batch.lote} está vencido!')
                        
                        # Calcular quantidade a retirar deste lote
                        quantidade_deste_lote = min(quantidade_restante, inventory.quantity_on_hand)
                        
                        # Atualizar estoque
                        inventory.quantity_on_hand -= quantidade_deste_lote
                        inventory.save()
                        
                        # Registrar movimentação
                        movimento = StockMovement.objects.create(
                            substance=substance,
                            batch=inventory.batch,
                            tipo='saida',
                            quantidade=quantidade_deste_lote,
                            motivo=form.cleaned_data.get('motivo', 'Saída de estoque'),
                            user=request.user,
                            paciente_nome=form.cleaned_data.get('paciente_nome', ''),
                            procedimento=form.cleaned_data.get('procedimento', ''),
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        )
                        movimentacoes_criadas.append(movimento)
                        
                        quantidade_restante -= quantidade_deste_lote
                    
                    messages.success(request, f'Saída registrada com sucesso! {len(movimentacoes_criadas)} lote(s) utilizados.')
                    return redirect('inventory:stock_exit')
                    
            except Exception as e:
                messages.error(request, f'Erro ao registrar saída: {str(e)}')
    else:
        form = StockExitForm()
    
    return render(request, 'inventory/stock_exit.html', {'form': form})


@login_required
@require_http_methods(["GET"])
def get_substance_stock(request):
    """
    API para buscar estoque atual de uma substância.
    """
    substance_id = request.GET.get('substance_id')
    if not substance_id:
        return JsonResponse({'error': 'ID da substância é obrigatório'}, status=400)
    
    try:
        substance = get_object_or_404(Substance, id=substance_id)
        
        # Buscar lotes disponíveis
        inventories = Inventory.objects.filter(
            substance=substance,
            quantity_on_hand__gt=0
        ).select_related('batch').order_by('batch__validade')
        
        lotes_data = []
        total_disponivel = Decimal('0')
        
        for inv in inventories:
            lotes_data.append({
                'lote': inv.batch.lote,
                'validade': inv.batch.validade.strftime('%d/%m/%Y'),
                'quantidade': float(inv.quantity_on_hand),
                'vencido': inv.batch.vencido,
                'vencendo_em_breve': inv.batch.vencendo_em_breve,
            })
            total_disponivel += inv.quantity_on_hand
        
        return JsonResponse({
            'total_disponivel': float(total_disponivel),
            'estoque_minimo': float(substance.estoque_minimo),
            'estoque_baixo': substance.estoque_baixo,
            'lotes': lotes_data,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def stock_movements_view(request):
    """
    View para consultar movimentações de estoque.
    """
    movements = StockMovement.objects.all().select_related(
        'substance', 'batch', 'user'
    ).order_by('-data_hora')[:100]  # Últimas 100 movimentações
    
    return render(request, 'inventory/stock_movements.html', {
        'movements': movements
    })
