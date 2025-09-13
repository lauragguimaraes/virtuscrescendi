from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class PatientSession(models.Model):
    """
    Modelo para controlar sessões numeradas de pacientes.
    """
    PAYMENT_STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('parcial', 'Parcial'),
        ('cancelado', 'Cancelado'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('transferencia', 'Transferência'),
        ('convenio', 'Convênio'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'Patient', 
        on_delete=models.CASCADE, 
        related_name='sessions',
        verbose_name='Paciente'
    )
    unit = models.ForeignKey(
        'Unit', 
        on_delete=models.CASCADE,
        verbose_name='Unidade'
    )
    session_number = models.PositiveIntegerField(verbose_name='Número da Sessão')
    session_date = models.DateField(verbose_name='Data da Sessão')
    
    # Protocolo e procedimento
    protocol_name = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name='Nome do Protocolo'
    )
    procedure_description = models.TextField(
        blank=True,
        verbose_name='Descrição do Procedimento'
    )
    
    # Controle financeiro
    total_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Valor Total'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pendente',
        verbose_name='Status do Pagamento'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        verbose_name='Forma de Pagamento'
    )
    payment_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Data do Pagamento'
    )
    payment_notes = models.TextField(
        blank=True,
        verbose_name='Observações do Pagamento'
    )
    
    # Observações clínicas
    clinical_notes = models.TextField(
        blank=True,
        verbose_name='Observações Clínicas'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='sessions_created',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Sessão do Paciente'
        verbose_name_plural = 'Sessões dos Pacientes'
        unique_together = ['patient', 'session_number']
        ordering = ['-session_date', '-session_number']
    
    def __str__(self):
        return f"{self.patient.nome} - Sessão {self.session_number} ({self.session_date})"
    
    @property
    def is_paid(self):
        return self.payment_status == 'pago'
    
    @property
    def substances_used(self):
        """Retorna as substâncias utilizadas nesta sessão."""
        from .models import StockMovement
        return StockMovement.objects.filter(
            paciente=self.patient,
            session=self
        ).select_related('substance')


class SessionSubstance(models.Model):
    """
    Modelo para controlar substâncias utilizadas em cada sessão.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        PatientSession, 
        on_delete=models.CASCADE,
        related_name='substances',
        verbose_name='Sessão'
    )
    substance = models.ForeignKey(
        'Substance', 
        on_delete=models.CASCADE,
        verbose_name='Substância'
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade'
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Unitário'
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Total'
    )
    
    # Observações específicas da substância na sessão
    notes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Substância da Sessão'
        verbose_name_plural = 'Substâncias das Sessões'
        unique_together = ['session', 'substance']
        ordering = ['substance__nome_comum']
    
    def __str__(self):
        return f"{self.session} - {self.substance.nome_comum} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calcular preço total automaticamente
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class ProtocolTemplate(models.Model):
    """
    Modelo para templates de protocolos clínicos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nome do Protocolo')
    description = models.TextField(blank=True, verbose_name='Descrição')
    
    # Configurações do protocolo
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    default_sessions = models.PositiveIntegerField(
        default=1,
        verbose_name='Número Padrão de Sessões'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='protocols_created',
        verbose_name='Criado por'
    )
    
    class Meta:
        verbose_name = 'Template de Protocolo'
        verbose_name_plural = 'Templates de Protocolos'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ProtocolSubstance(models.Model):
    """
    Modelo para substâncias padrão de um protocolo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey(
        ProtocolTemplate, 
        on_delete=models.CASCADE,
        related_name='substances',
        verbose_name='Protocolo'
    )
    substance = models.ForeignKey(
        'Substance', 
        on_delete=models.CASCADE,
        verbose_name='Substância'
    )
    default_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade Padrão'
    )
    is_optional = models.BooleanField(
        default=False,
        verbose_name='Opcional'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    
    class Meta:
        verbose_name = 'Substância do Protocolo'
        verbose_name_plural = 'Substâncias dos Protocolos'
        unique_together = ['protocol', 'substance']
        ordering = ['order', 'substance__nome_comum']
    
    def __str__(self):
        return f"{self.protocol.name} - {self.substance.nome_comum}"

