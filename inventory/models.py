from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Unit(models.Model):
    """
    Modelo para unidades/filiais da clínica.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome da Unidade')
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    endereco = models.TextField(blank=True, verbose_name='Endereço')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    responsavel = models.CharField(max_length=100, blank=True, verbose_name='Responsável')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.codigo})"


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
    
    # Configurações de alerta (podem variar por unidade)
    estoque_minimo_default = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('1.0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Estoque Mínimo Padrão'
    )
    
    # Controle financeiro
    preco_padrao = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Padrão por Unidade'
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
    
    def __str__(self):
        return f"{self.nome_comum} - {self.concentracao}"
    
    @property
    def estoque_minimo(self):
        """Mantém compatibilidade com código existente"""
        return self.estoque_minimo_default
    
    def get_estoque_total(self):
        """Retorna estoque total em todas as unidades"""
        return sum(
            inv.quantity_on_hand 
            for inv in self.inventory_set.all()
        )
    
    def get_estoque_por_unidade(self):
        """Retorna dicionário com estoque por unidade"""
        estoque = {}
        for inv in self.inventory_set.select_related('unit'):
            unit_name = inv.unit.nome if inv.unit else 'Sem Unidade'
            if unit_name not in estoque:
                estoque[unit_name] = Decimal('0')
            estoque[unit_name] += inv.quantity_on_hand
        return estoque
    
    @property
    def estoque_baixo(self):
        """Verifica se alguma unidade está com estoque baixo"""
        for inv in self.inventory_set.all():
            estoque_minimo = inv.get_estoque_minimo()
            if inv.quantity_on_hand <= estoque_minimo:
                return True
        return False


class SubstanceUnitConfig(models.Model):
    """
    Configurações específicas de substância por unidade.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name='Unidade')
    estoque_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Estoque Mínimo'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo nesta Unidade')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Configuração por Unidade'
        verbose_name_plural = 'Configurações por Unidade'
        unique_together = ['substance', 'unit']
    
    def __str__(self):
        return f"{self.substance.nome_comum} - {self.unit.nome}"


class Patient(models.Model):
    """
    Modelo para pacientes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código do Paciente')
    nome = models.CharField(max_length=200, verbose_name='Nome')
    data_nascimento = models.DateField(null=True, blank=True, verbose_name='Data de Nascimento')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Unidade principal de atendimento
    unidade_principal = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Unidade Principal'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='patients_created',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Batch(models.Model):
    """
    Modelo para lotes de substâncias.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name='Unidade')
    lote = models.CharField(max_length=100, verbose_name='Número do Lote')
    validade = models.DateField(verbose_name='Data de Validade')
    quantidade_recebida = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade Recebida'
    )
    fornecedor = models.CharField(max_length=200, verbose_name='Fornecedor')
    nota_fiscal_ref = models.CharField(max_length=100, blank=True, verbose_name='Referência NF')
    preco_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Unitário'
    )
    
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
        unique_together = ['lote', 'substance', 'unit']  # Mesmo lote pode existir em unidades diferentes
        ordering = ['validade', 'lote']
    
    def __str__(self):
        return f"{self.lote} - {self.substance.nome_comum} ({self.unit.codigo})"
    
    @property
    def vencido(self):
        return self.validade < timezone.now().date()
    
    @property
    def vencendo_em_breve(self):
        dias_restantes = (self.validade - timezone.now().date()).days
        return 0 < dias_restantes <= self.substance.dias_alerta_vencimento
    
    @property
    def preco_total(self):
        return self.quantidade_recebida * self.preco_unitario
    
    def get_estoque_atual(self):
        """Retorna o estoque atual deste lote"""
        try:
            inventory = Inventory.objects.get(batch=self, unit=self.unit)
            return inventory.quantity_on_hand
        except Inventory.DoesNotExist:
            return Decimal('0')


class Inventory(models.Model):
    """
    Modelo para controle de estoque atual por unidade.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, verbose_name='Lote')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name='Unidade')
    quantity_on_hand = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Quantidade em Estoque'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Estoque'
        verbose_name_plural = 'Estoque'
        unique_together = ['substance', 'batch', 'unit']
        ordering = ['batch__validade', 'substance__nome_comum']
    
    def __str__(self):
        return f"{self.substance.nome_comum} - {self.batch.lote} ({self.unit.codigo}) - {self.quantity_on_hand}"
    
    def get_estoque_minimo(self):
        """Retorna estoque mínimo específico da unidade ou padrão"""
        try:
            config = SubstanceUnitConfig.objects.get(
                substance=self.substance, 
                unit=self.unit
            )
            return config.estoque_minimo
        except SubstanceUnitConfig.DoesNotExist:
            return self.substance.estoque_minimo_default
    
    @property
    def estoque_baixo(self):
        return self.quantity_on_hand <= self.get_estoque_minimo()


class StockMovement(models.Model):
    """
    Modelo para log de movimentações de estoque (imutável).
    """
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('correcao', 'Correção'),
        ('ajuste', 'Ajuste'),
        ('perda', 'Perda'),
        ('transferencia_saida', 'Transferência - Saída'),
        ('transferencia_entrada', 'Transferência - Entrada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, verbose_name='Lote')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, verbose_name='Unidade')
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES, verbose_name='Tipo')
    quantidade = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade'
    )
    motivo = models.TextField(verbose_name='Motivo')
    
    # Informações do paciente (para saídas)
    paciente = models.ForeignKey(
        Patient, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Paciente'
    )
    paciente_nome = models.CharField(max_length=200, blank=True, verbose_name='Nome do Paciente')
    procedimento = models.TextField(blank=True, verbose_name='Procedimento')
    
    # Vinculação com sessão do paciente
    session = models.ForeignKey(
        'PatientSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements',
        verbose_name='Sessão'
    )
    
    # Informações de transferência
    unidade_destino = models.ForeignKey(
        Unit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transferencias_recebidas',
        verbose_name='Unidade Destino'
    )
    
    # Audit fields (imutáveis)
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data_hora']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.substance.nome_comum} - {self.quantidade} ({self.unit.codigo})"


class UnitTransfer(models.Model):
    """
    Modelo para transferências entre unidades.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_transito', 'Em Trânsito'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código da Transferência')
    unidade_origem = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='transferencias_enviadas',
        verbose_name='Unidade Origem'
    )
    unidade_destino = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='transferencias_recebidas_transfer',
        verbose_name='Unidade Destino'
    )
    substance = models.ForeignKey(Substance, on_delete=models.CASCADE, verbose_name='Substância')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, verbose_name='Lote')
    quantidade = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade'
    )
    motivo = models.TextField(verbose_name='Motivo da Transferência')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    
    # Datas importantes
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_envio = models.DateTimeField(null=True, blank=True, verbose_name='Data do Envio')
    data_recebimento = models.DateTimeField(null=True, blank=True, verbose_name='Data do Recebimento')
    
    # Usuários responsáveis
    solicitado_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='transferencias_solicitadas',
        verbose_name='Solicitado por'
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
        verbose_name = 'Transferência entre Unidades'
        verbose_name_plural = 'Transferências entre Unidades'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        return f"{self.codigo} - {self.unidade_origem.codigo} → {self.unidade_destino.codigo}"


# Importar modelos de sessão
from .models_session import PatientSession, SessionSubstance, ProtocolTemplate, ProtocolSubstance



# Modelos de Transferência Nova
class TransferNew(models.Model):
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
        Unit, 
        on_delete=models.CASCADE, 
        related_name='transfers_enviadas',
        verbose_name='Unidade de Origem'
    )
    unidade_destino = models.ForeignKey(
        Unit, 
        on_delete=models.CASCADE, 
        related_name='transfers_recebidas',
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
        related_name='transfers_criadas',
        verbose_name='Criado por'
    )
    enviado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transfers_enviadas',
        verbose_name='Enviado por'
    )
    recebido_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transfers_recebidas',
        verbose_name='Recebido por'
    )
    
    class Meta:
        verbose_name = 'Transferência Nova'
        verbose_name_plural = 'Transferências Novas'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.numero} - {self.unidade_origem} → {self.unidade_destino}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar número automático
            ultimo_numero = TransferNew.objects.filter(
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


class TransferItemNew(models.Model):
    """
    Itens de uma transferência.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transfer = models.ForeignKey(
        TransferNew, 
        on_delete=models.CASCADE, 
        related_name='itens',
        verbose_name='Transferência'
    )
    substance = models.ForeignKey(
        Substance, 
        on_delete=models.CASCADE,
        verbose_name='Substância'
    )
    batch_origem = models.ForeignKey(
        Batch, 
        on_delete=models.CASCADE,
        related_name='transfers_saida',
        verbose_name='Lote de Origem'
    )
    batch_destino = models.ForeignKey(
        Batch, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='transfers_entrada',
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
        verbose_name = 'Item de Transferência Nova'
        verbose_name_plural = 'Itens de Transferência Nova'
    
    def __str__(self):
        return f"{self.substance.nome_comum} - {self.quantidade}"



# Modelo para Termos de Responsabilidade
class ResponsibilityTerm(models.Model):
    """
    Modelo para termos de responsabilidade de substâncias controladas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=20, unique=True, verbose_name='Número do Termo')
    
    # Dados do paciente
    patient = models.ForeignKey(
        'Patient', 
        on_delete=models.CASCADE,
        verbose_name='Paciente'
    )
    
    # Dados da substância
    substance = models.ForeignKey(
        'Substance', 
        on_delete=models.CASCADE,
        verbose_name='Substância'
    )
    
    # Dados da aplicação
    unit = models.ForeignKey(
        'Unit', 
        on_delete=models.CASCADE,
        verbose_name='Unidade'
    )
    
    # Dados médicos
    medico_responsavel = models.ForeignKey(
        'ResponsibleDoctor',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Médico Responsável'
    )
    
    # Template usado
    template_usado = models.ForeignKey(
        'TermTemplate',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Template Utilizado'
    )
    
    # Dados da aplicação
    data_aplicacao = models.DateField(
        default=timezone.now,
        verbose_name='Data da Aplicação'
    )
    dosagem = models.CharField(
        max_length=100,
        verbose_name='Dosagem'
    )
    via_administracao = models.CharField(
        max_length=100,
        default='Subcutânea',
        verbose_name='Via de Administração'
    )
    
    # Observações e riscos
    observacoes_medicas = models.TextField(
        blank=True,
        verbose_name='Observações Médicas'
    )
    
    # Dados de quem aplicou
    aplicado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='termos_aplicados',
        verbose_name='Aplicado por'
    )
    
    # Dados de quem gerou o termo
    gerado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='termos_gerados',
        verbose_name='Gerado por'
    )
    
    # Controle
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Geração')
    assinado = models.BooleanField(default=False, verbose_name='Assinado pelo Paciente')
    data_assinatura = models.DateTimeField(null=True, blank=True, verbose_name='Data da Assinatura')
    
    # Campos específicos para substâncias controladas
    receita_medica = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Número da Receita Médica'
    )
    data_receita = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Data da Receita'
    )
    
    class Meta:
        verbose_name = 'Termo de Responsabilidade'
        verbose_name_plural = 'Termos de Responsabilidade'
        ordering = ['-data_geracao']
    
    def __str__(self):
        return f"{self.numero} - {self.patient.nome} - {self.substance.nome_comum}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar número automático
            ultimo_numero = ResponsibilityTerm.objects.filter(
                numero__startswith='TR'
            ).count()
            self.numero = f'TR{ultimo_numero + 1:06d}'
        super().save(*args, **kwargs)
    
    @property
    def is_controlled_substance(self):
        """Verifica se a substância é controlada"""
        controlled_substances = [
            'mounjaro', 'ozempic', 'saxenda', 'victoza', 
            'trulicity', 'rybelsus', 'wegovy'
        ]
        return any(controlled in self.substance.nome_comum.lower() 
                  for controlled in controlled_substances)
    
    @property
    def requires_special_care(self):
        """Verifica se requer cuidados especiais"""
        return self.is_controlled_substance


# Modelo para Médicos Responsáveis
class ResponsibleDoctor(models.Model):
    """
    Modelo para cadastro de médicos responsáveis pelos protocolos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, verbose_name='Nome Completo')
    crm = models.CharField(max_length=20, verbose_name='CRM')
    especialidade = models.CharField(max_length=100, blank=True, verbose_name='Especialidade')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Dados de contato
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    email = models.EmailField(blank=True, verbose_name='Email')
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Médico Responsável'
        verbose_name_plural = 'Médicos Responsáveis'
        ordering = ['nome']
    
    def __str__(self):
        return f"Dr. {self.nome} - CRM {self.crm}"

# Modelo para Templates de Termos Editáveis
class TermTemplate(models.Model):
    """
    Template editável para termos de responsabilidade.
    Baseado nos exemplos fornecidos pela usuária.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, verbose_name='Nome do Template')
    
    # Tipo de template
    TIPO_CHOICES = [
        ('full_care', 'Protocolo Full Care'),
        ('injetavel_geral', 'Injetáveis em Geral'),
        ('controlada', 'Substâncias Controladas'),
        ('personalizado', 'Personalizado'),
    ]
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='full_care',
        verbose_name='Tipo de Template'
    )
    
    # Conteúdo editável do termo
    titulo = models.CharField(
        max_length=300,
        default='TERMO DE CONSENTIMENTO LIVRE, ESCLARECIDO E DECLARAÇÃO DE RESPONSABILIDADE',
        verbose_name='Título do Termo'
    )
    
    conteudo = models.TextField(
        verbose_name='Conteúdo do Termo',
        help_text='''
        Variáveis disponíveis:
        {{PACIENTE_NOME}} - Nome do paciente
        {{PACIENTE_RG}} - RG do paciente  
        {{PACIENTE_CPF}} - CPF do paciente
        {{PACIENTE_ENDERECO}} - Endereço do paciente
        {{MEDICO_NOME}} - Nome do médico responsável
        {{MEDICO_CRM}} - CRM do médico
        {{PROTOCOLO_NOME}} - Nome do protocolo (ex: Full Care)
        {{MEDICAMENTOS}} - Lista de medicamentos
        {{LOCAL}} - Local (Ribeirão Preto/SP ou Bauru/SP)
        {{DATA_ATUAL}} - Data atual
        {{DATA_ENTREGA}} - Data da entrega dos medicamentos
        '''
    )
    
    # Controle de versão
    versao = models.CharField(max_length=10, default='1.0', verbose_name='Versão')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Metadados
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='term_templates_criados',
        verbose_name='Criado por'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='term_templates_modificados',
        verbose_name='Modificado por'
    )
    data_modificacao = models.DateTimeField(auto_now=True, verbose_name='Última Modificação')
    
    observacoes_versao = models.TextField(
        blank=True,
        verbose_name='Observações da Versão',
        help_text='Descreva as mudanças jurídicas ou atualizações feitas'
    )
    
    class Meta:
        verbose_name = 'Template de Termo'
        verbose_name_plural = 'Templates de Termos'
        ordering = ['-data_modificacao']
    
    def __str__(self):
        return f"{self.nome} (v{self.versao})"
    
    def render_content(self, context):
        """
        Renderiza o conteúdo substituindo as variáveis pelos dados reais.
        """
        content = self.conteudo
        
        replacements = {
            '{{PACIENTE_NOME}}': context.get('paciente_nome', ''),
            '{{PACIENTE_RG}}': context.get('paciente_rg', ''),
            '{{PACIENTE_CPF}}': context.get('paciente_cpf', ''),
            '{{PACIENTE_ENDERECO}}': context.get('paciente_endereco', ''),
            '{{MEDICO_NOME}}': context.get('medico_nome', ''),
            '{{MEDICO_CRM}}': context.get('medico_crm', ''),
            '{{PROTOCOLO_NOME}}': context.get('protocolo_nome', 'Full Care'),
            '{{MEDICAMENTOS}}': context.get('medicamentos', ''),
            '{{LOCAL}}': context.get('local', ''),
            '{{DATA_ATUAL}}': context.get('data_atual', timezone.now().strftime('%d de %B de %Y')),
            '{{DATA_ENTREGA}}': context.get('data_entrega', ''),
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        return content

