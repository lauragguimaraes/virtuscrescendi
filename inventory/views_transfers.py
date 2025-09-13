from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import TransferNew, TransferItemNew, Unit, Substance, Batch, StockMovement

@login_required
def transfers_list(request):
    """Lista todas as transferências"""
    transfers = TransferNew.objects.select_related(
        'unidade_origem', 'unidade_destino', 'criado_por'
    ).prefetch_related('itens__substance').order_by('-data_criacao')
    
    context = {
        'transfers': transfers,
        'title': 'Transferências entre Unidades'
    }
    return render(request, 'inventory/transfers_list.html', context)

@login_required
def transfer_create(request):
    """Criar nova transferência"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Dados da transferência
                unidade_origem_id = request.POST.get('unidade_origem')
                unidade_destino_id = request.POST.get('unidade_destino')
                observacoes = request.POST.get('observacoes', '')
                
                # Validações básicas
                if unidade_origem_id == unidade_destino_id:
                    messages.error(request, 'Unidade de origem e destino devem ser diferentes!')
                    return redirect('transfer_create')
                
                unidade_origem = get_object_or_404(Unit, id=unidade_origem_id)
                unidade_destino = get_object_or_404(Unit, id=unidade_destino_id)
                
                # Criar transferência
                transfer = TransferNew.objects.create(
                    unidade_origem=unidade_origem,
                    unidade_destino=unidade_destino,
                    observacoes=observacoes,
                    criado_por=request.user
                )
                
                # Processar itens
                substances = request.POST.getlist('substance[]')
                quantities = request.POST.getlist('quantity[]')
                
                if not substances or not quantities:
                    messages.error(request, 'Adicione pelo menos um item à transferência!')
                    transfer.delete()
                    return redirect('transfer_create')
                
                for substance_id, quantity in zip(substances, quantities):
                    if substance_id and quantity:
                        substance = get_object_or_404(Substance, id=substance_id)
                        quantity = Decimal(str(quantity))
                        
                        # Buscar lote de origem
                        batch_origem = Batch.objects.filter(
                            substance=substance,
                            unit=unidade_origem
                        ).first()
                        
                        if not batch_origem:
                            messages.error(request, f'Lote não encontrado para {substance.nome_comum} na unidade {unidade_origem.nome}!')
                            transfer.delete()
                            return redirect('transfer_create')
                        
                        if batch_origem.get_estoque_atual() < quantity:
                            messages.error(request, f'Estoque insuficiente de {substance.nome_comum}! Disponível: {batch_origem.get_estoque_atual()}')
                            transfer.delete()
                            return redirect('transfer_create')
                        
                        # Buscar ou criar lote de destino
                        batch_destino, created = Batch.objects.get_or_create(
                            substance=substance,
                            unit=unidade_destino,
                            defaults={
                                'lote': f'TRANSF-{transfer.numero}',
                                'data_fabricacao': timezone.now().date(),
                                'data_validade': timezone.now().date().replace(year=timezone.now().year + 2),
                                'quantidade_inicial': Decimal('0'),
                                'preco_unitario': batch_origem.preco_unitario if hasattr(batch_origem, 'preco_unitario') else Decimal('0')
                            }
                        )
                        
                        # Criar item da transferência
                        TransferItemNew.objects.create(
                            transfer=transfer,
                            substance=substance,
                            batch_origem=batch_origem,
                            batch_destino=batch_destino,
                            quantidade=quantity
                        )
                        
                        # Criar movimentações de estoque
                        # Saída da origem
                        StockMovement.objects.create(
                            substance=substance,
                            batch=batch_origem,
                            unit=unidade_origem,
                            tipo='saida',
                            quantidade=quantity,
                            user=request.user,
                            data_hora=timezone.now()
                        )
                        
                        # Entrada no destino
                        StockMovement.objects.create(
                            substance=substance,
                            batch=batch_destino,
                            unit=unidade_destino,
                            tipo='entrada',
                            quantidade=quantity,
                            user=request.user,
                            data_hora=timezone.now()
                        )
                        
                        # Atualizar estoques
                        batch_origem.quantidade_inicial -= quantity
                        batch_origem.save()
                        
                        batch_destino.quantidade_inicial += quantity
                        batch_destino.save()
                
                # Marcar transferência como concluída
                transfer.status = 'concluida'
                transfer.data_envio = timezone.now()
                transfer.data_recebimento = timezone.now()
                transfer.enviado_por = request.user
                transfer.recebido_por = request.user
                transfer.save()
                
                messages.success(request, f'Transferência {transfer.numero} criada com sucesso!')
                return redirect('transfer_detail', transfer_id=transfer.id)
                
        except Exception as e:
            messages.error(request, f'Erro ao criar transferência: {str(e)}')
            return redirect('transfer_create')
    
    # GET request
    units = Unit.objects.filter(ativo=True)
    substances = Substance.objects.all().order_by('nome_comum')
    
    context = {
        'units': units,
        'substances': substances,
        'title': 'Nova Transferência'
    }
    return render(request, 'inventory/transfer_create.html', context)

@login_required
def transfer_detail(request, transfer_id):
    """Detalhes de uma transferência"""
    transfer = get_object_or_404(
        TransferNew.objects.select_related(
            'unidade_origem', 'unidade_destino', 'criado_por', 'enviado_por', 'recebido_por'
        ).prefetch_related('itens__substance', 'itens__batch_origem', 'itens__batch_destino'),
        id=transfer_id
    )
    
    context = {
        'transfer': transfer,
        'title': f'Transferência {transfer.numero}'
    }
    return render(request, 'inventory/transfer_detail.html', context)

@login_required
def get_substance_stock(request):
    """API para obter estoque de uma substância em uma unidade"""
    substance_id = request.GET.get('substance_id')
    unit_id = request.GET.get('unit_id')
    
    if not substance_id or not unit_id:
        return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)
    
    try:
        batch = Batch.objects.filter(
            substance_id=substance_id,
            unit_id=unit_id
        ).first()
        
        if batch:
            stock = batch.get_estoque_atual()
            return JsonResponse({
                'stock': float(stock),
                'batch_id': str(batch.id)
            })
        else:
            return JsonResponse({'stock': 0, 'batch_id': None})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

