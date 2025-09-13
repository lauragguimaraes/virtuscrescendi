from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Substance(models.Model):
    """
    Modelo para substâncias/medicamentos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome_comum = models.CharField(max_length=200, verbose_name='Nome Comum')
    nome_comercial = models.CharField(max_length=200, blank=True, verbose_name='Nome Comercial')
    concentracao = models.CharField(max_length=100, verbose_name='Concentração')
    apresentacao = models.CharField(max_length=100, verbose_name='Apresentação')
    unidade = models.CharField(max_length=50, default='ampola', verbose_name='Unidade')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    # Configurações de alerta
    estoque_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Estoque Mínimo'
    )
    dias_alerta_vencimento = models.IntegerField(
        default=90,
        validators=[MinValueValidator(1)],
        verbose_name='Dias para Alerta de Vencimento'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='substances_created',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Substância'
        verbose_name_plural = 'Substâncias'
        ordering = ['nome_comum']
        unique_together = ['nome_comum', 'concentracao']
    
    def __str__(self):
        return f"{self.nome_comum} - {self.concentracao}"
    
    @property
    def estoque_atual(self):
        """Retorna o estoque atual total da substância."""
        return sum(
            inventory.quantity_on_hand 
            for inventory in self.inventory_set.all()
        )
    
    @property
    def lotes_vencendo(self):
        """Retorna lotes que estão próximos do vencimento."""
        data_limite = timezone.now().date() + timezone.timedelta(days=self.dias_alerta_vencimento)
        return self.batch_set.filter(
            validade__lte=data_limite,
            inventory__quantity_on_hand__gt=0
        ).distinct()
    
    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo."""
        return self.estoque_atual < self.estoque_minimo


class Batch(models.Model):
    """
    Modelo para lotes de substâncias.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    lote = models.CharField(max_length=100, verbose_name='Número do Lote')
    validade = models.DateField(verbose_name='Data de Validade')
    quantidade_recebida = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Quantidade Recebida'
    )
    
    # Informações do fornecedor
    fornecedor = models.CharField(max_length=200, verbose_name='Fornecedor')
    nota_fiscal_ref = models.CharField(max_length=100, blank=True, verbose_name='Referência da NF')
    preco_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Unitário'
    )
    
    # Armazenamento
    local_armazenamento = models.CharField(
        max_length=100, 
        default='armário',
        verbose_name='Local de Armazenamento'
    )
    refrigerado = models.BooleanField(default=False, verbose_name='Refrigerado')
    
    # Datas de fabricação (opcional)
    data_fabricacao = models.DateField(blank=True, null=True, verbose_name='Data de Fabricação')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='batches_created',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['validade', 'lote']
        unique_together = ['substance', 'lote']
    
    def __str__(self):
        return f"{self.substance.nome_comum} - Lote {self.lote}"
    
    @property
    def quantidade_disponivel(self):
        """Retorna a quantidade disponível no estoque."""
        try:
            return self.inventory.quantity_on_hand
        except Inventory.DoesNotExist:
            return Decimal('0')
    
    @property
    def vencido(self):
        """Verifica se o lote está vencido."""
        return self.validade < timezone.now().date()
    
    @property
    def vencendo_em_breve(self):
        """Verifica se o lote está próximo do vencimento."""
        dias_limite = self.substance.dias_alerta_vencimento
        data_limite = timezone.now().date() + timezone.timedelta(days=dias_limite)
        return self.validade <= data_limite


class Inventory(models.Model):
    """
    Modelo para controle de estoque atual por lote.
    Separado das movimentações para otimizar consultas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, verbose_name='Lote')
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    quantity_on_hand = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Quantidade em Estoque'
    )
    
    # Audit fields
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    
    class Meta:
        verbose_name = 'Estoque'
        verbose_name_plural = 'Estoques'
        ordering = ['batch__validade']
    
    def __str__(self):
        return f"{self.substance.nome_comum} - {self.batch.lote}: {self.quantity_on_hand}"


class StockMovement(models.Model):
    """
    Modelo para registrar todas as movimentações de estoque.
    Log imutável de todas as transações.
    """
    MOVEMENT_TYPES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('correcao', 'Correção'),
        ('ajuste', 'Ajuste'),
        ('perda', 'Perda'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, verbose_name='Lote')
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    tipo = models.CharField(max_length=20, choices=MOVEMENT_TYPES, verbose_name='Tipo')
    quantidade = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Quantidade'
    )
    
    # Informações do usuário e data
    data_hora = models.DateTimeField(default=timezone.now, verbose_name='Data/Hora')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Usuário')
    
    # Informações do paciente (para saídas)
    paciente_id = models.CharField(max_length=100, blank=True, verbose_name='ID do Paciente')
    paciente_nome = models.CharField(max_length=200, blank=True, verbose_name='Nome do Paciente')
    procedimento = models.TextField(blank=True, verbose_name='Procedimento')
    registro_clinico_ref = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='Referência do Registro Clínico'
    )
    
    # Documentos e observações
    documento_ref = models.CharField(max_length=100, blank=True, verbose_name='Documento de Referência')
    motivo = models.TextField(blank=True, verbose_name='Motivo/Observações')
    
    # Para correções - referência ao movimento original
    registro_origem = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Registro de Origem'
    )
    
    # Audit fields
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    class Meta:
        verbose_name = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering = ['-data_hora']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.substance.nome_comum} - {self.quantidade}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o save para atualizar automaticamente o estoque.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.update_inventory()
    
    def update_inventory(self):
        """
        Atualiza o registro de estoque baseado na movimentação.
        """
        inventory, created = Inventory.objects.get_or_create(
            batch=self.batch,
            substance=self.substance,
            defaults={'quantity_on_hand': Decimal('0')}
        )
        
        if self.tipo == 'entrada':
            inventory.quantity_on_hand += self.quantidade
        elif self.tipo in ['saida', 'perda']:
            inventory.quantity_on_hand -= self.quantidade
        elif self.tipo == 'correcao':
            # Para correções, a quantidade pode ser positiva ou negativa
            inventory.quantity_on_hand += self.quantidade
        elif self.tipo == 'ajuste':
            # Para ajustes, definir a quantidade exata
            inventory.quantity_on_hand = self.quantidade
        
        # Garantir que não fique negativo
        if inventory.quantity_on_hand < 0:
            inventory.quantity_on_hand = Decimal('0')
        
        inventory.save()


class Patient(models.Model):
    """
    Modelo minimalista para pacientes (LGPD compliant).
    Armazena apenas o mínimo necessário para o controle de estoque.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_interno = models.CharField(max_length=100, unique=True, verbose_name='ID Interno')
    nome = models.CharField(max_length=200, verbose_name='Nome')
    data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')
    contato = models.CharField(max_length=100, blank=True, verbose_name='Contato')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.id_interno} - {self.nome}"
