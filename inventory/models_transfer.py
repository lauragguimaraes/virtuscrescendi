from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()

class Transfer(models.Model):
    """
    Modelo para transferências de substâncias entre unidades.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_transito', 'Em Trânsito'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número da Transferência')
    
    # Unidades origem e destino
    unidade_origem = models.ForeignKey(
        'Unit', 
        on_delete=models.CASCADE, 
        related_name='transferencias_enviadas',
        verbose_name='Unidade de Origem'
    )
    unidade_destino = models.ForeignKey(
        'Unit', 
        on_delete=models.CASCADE, 
        related_name='transferencias_recebidas',
        verbose_name='Unidade de Destino'
    )
    
    # Status e datas
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente',
        verbose_name='Status'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_envio = models.DateTimeField(null=True, blank=True, verbose_name='Data de Envio')
    data_recebimento = models.DateTimeField(null=True, blank=True, verbose_name='Data de Recebimento')
    
    # Observações
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    # Usuários responsáveis
    criado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='transferencias_criadas',
        verbose_name='Criado por'
    )
    enviado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transferencias_enviadas',
        verbose_name='Enviado por'
    )
    recebido_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transferencias_recebidas',
        verbose_name='Recebido por'
    )
    
    class Meta:
        verbose_name = 'Transferência'
        verbose_name_plural = 'Transferências'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.numero} - {self.unidade_origem} → {self.unidade_destino}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar número automático
            ultimo_numero = Transfer.objects.filter(
                numero__startswith='TRF'
            ).count()
            self.numero = f'TRF{ultimo_numero + 1:04d}'
        super().save(*args, **kwargs)
    
    @property
    def total_itens(self):
        """Retorna total de itens na transferência"""
        return self.itens.count()
    
    @property
    def total_quantidade(self):
        """Retorna quantidade total transferida"""
        return sum(item.quantidade for item in self.itens.all())


class TransferItem(models.Model):
    """
    Itens de uma transferência.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transfer = models.ForeignKey(
        Transfer, 
        on_delete=models.CASCADE, 
        related_name='itens',
        verbose_name='Transferência'
    )
    substance = models.ForeignKey(
        'Substance', 
        on_delete=models.CASCADE,
        verbose_name='Substância'
    )
    batch_origem = models.ForeignKey(
        'Batch', 
        on_delete=models.CASCADE,
        related_name='transferencias_saida',
        verbose_name='Lote de Origem'
    )
    batch_destino = models.ForeignKey(
        'Batch', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='transferencias_entrada',
        verbose_name='Lote de Destino'
    )
    quantidade = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    class Meta:
        verbose_name = 'Item de Transferência'
        verbose_name_plural = 'Itens de Transferência'
    
    def __str__(self):
        return f"{self.substance.nome_comum} - {self.quantidade}"

