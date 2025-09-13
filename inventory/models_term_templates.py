from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class TermTemplate(models.Model):
    """
    Template editável para termos de responsabilidade.
    Permite atualizações jurídicas ao longo do tempo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, verbose_name='Nome do Template')
    
    # Tipo de substância/situação
    TIPO_CHOICES = [
        ('geral', 'Geral (Todas as substâncias)'),
        ('controlada', 'Substâncias Controladas'),
        ('mounjaro', 'Mounjaro/Ozempic'),
        ('injetavel', 'Injetáveis em Geral'),
        ('especifico', 'Substância Específica'),
    ]
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='geral',
        verbose_name='Tipo de Template'
    )
    
    # Substância específica (opcional)
    substance = models.ForeignKey(
        'Substance',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Substância Específica'
    )
    
    # Conteúdo do termo (editável)
    conteudo = models.TextField(
        verbose_name='Conteúdo do Termo',
        help_text='''
        Use as seguintes variáveis que serão substituídas automaticamente:
        {{PACIENTE_NOME}} - Nome do paciente
        {{PACIENTE_CPF}} - CPF do paciente
        {{PACIENTE_ENDERECO}} - Endereço do paciente
        {{PACIENTE_TELEFONE}} - Telefone do paciente
        {{SUBSTANCIA_NOME}} - Nome da substância
        {{SUBSTANCIA_CONCENTRACAO}} - Concentração da substância
        {{DATA_APLICACAO}} - Data da aplicação
        {{DOSAGEM}} - Dosagem aplicada
        {{MEDICO_NOME}} - Nome do médico responsável
        {{MEDICO_CRM}} - CRM do médico
        {{UNIDADE_NOME}} - Nome da unidade
        {{PROFISSIONAL_NOME}} - Nome do profissional que aplicou
        {{DATA_ATUAL}} - Data atual
        {{NUMERO_TERMO}} - Número do termo
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
        related_name='templates_criados',
        verbose_name='Criado por'
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    
    # Última modificação
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='templates_modificados',
        verbose_name='Modificado por'
    )
    data_modificacao = models.DateTimeField(auto_now=True, verbose_name='Última Modificação')
    
    # Observações sobre mudanças
    observacoes_versao = models.TextField(
        blank=True,
        verbose_name='Observações da Versão',
        help_text='Descreva as mudanças feitas nesta versão'
    )
    
    class Meta:
        verbose_name = 'Template de Termo'
        verbose_name_plural = 'Templates de Termos'
        ordering = ['-data_modificacao']
        unique_together = ['tipo', 'substance', 'versao']
    
    def __str__(self):
        if self.substance:
            return f"{self.nome} - {self.substance.nome_comum} (v{self.versao})"
        return f"{self.nome} - {self.get_tipo_display()} (v{self.versao})"
    
    def get_template_for_substance(substance):
        """
        Busca o template mais específico para uma substância.
        Ordem de prioridade:
        1. Template específico para a substância
        2. Template para substâncias controladas (se aplicável)
        3. Template geral para injetáveis
        4. Template geral
        """
        # 1. Template específico
        template = TermTemplate.objects.filter(
            tipo='especifico',
            substance=substance,
            ativo=True
        ).first()
        
        if template:
            return template
        
        # 2. Template para controladas
        controlled_substances = [
            'mounjaro', 'ozempic', 'saxenda', 'victoza', 
            'trulicity', 'rybelsus', 'wegovy'
        ]
        
        if any(controlled in substance.nome_comum.lower() for controlled in controlled_substances):
            template = TermTemplate.objects.filter(
                tipo='controlada',
                ativo=True
            ).first()
            
            if template:
                return template
            
            # Template específico para Mounjaro/Ozempic
            if any(med in substance.nome_comum.lower() for med in ['mounjaro', 'ozempic']):
                template = TermTemplate.objects.filter(
                    tipo='mounjaro',
                    ativo=True
                ).first()
                
                if template:
                    return template
        
        # 3. Template para injetáveis
        template = TermTemplate.objects.filter(
            tipo='injetavel',
            ativo=True
        ).first()
        
        if template:
            return template
        
        # 4. Template geral
        return TermTemplate.objects.filter(
            tipo='geral',
            ativo=True
        ).first()
    
    def render_content(self, context):
        """
        Renderiza o conteúdo do template substituindo as variáveis.
        """
        content = self.conteudo
        
        # Substituir variáveis
        replacements = {
            '{{PACIENTE_NOME}}': context.get('paciente_nome', ''),
            '{{PACIENTE_CPF}}': context.get('paciente_cpf', ''),
            '{{PACIENTE_ENDERECO}}': context.get('paciente_endereco', ''),
            '{{PACIENTE_TELEFONE}}': context.get('paciente_telefone', ''),
            '{{SUBSTANCIA_NOME}}': context.get('substancia_nome', ''),
            '{{SUBSTANCIA_CONCENTRACAO}}': context.get('substancia_concentracao', ''),
            '{{DATA_APLICACAO}}': context.get('data_aplicacao', ''),
            '{{DOSAGEM}}': context.get('dosagem', ''),
            '{{MEDICO_NOME}}': context.get('medico_nome', ''),
            '{{MEDICO_CRM}}': context.get('medico_crm', ''),
            '{{UNIDADE_NOME}}': context.get('unidade_nome', ''),
            '{{PROFISSIONAL_NOME}}': context.get('profissional_nome', ''),
            '{{DATA_ATUAL}}': context.get('data_atual', timezone.now().strftime('%d/%m/%Y')),
            '{{NUMERO_TERMO}}': context.get('numero_termo', ''),
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        return content

