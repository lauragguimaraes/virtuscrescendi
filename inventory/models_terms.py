from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

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
    medico_responsavel = models.CharField(
        max_length=200, 
        verbose_name='Médico Responsável'
    )
    crm_medico = models.CharField(
        max_length=20, 
        verbose_name='CRM do Médico'
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

