from django import forms
from django.forms import inlineformset_factory
from .models import ProtocolTemplate, ProtocolSubstance, Substance


class ProtocolTemplateForm(forms.ModelForm):
    class Meta:
        model = ProtocolTemplate
        fields = ['name', 'description', 'default_sessions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Protocolo Antioxidante'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descrição detalhada do protocolo...'
            }),
            'default_sessions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nome do Protocolo',
            'description': 'Descrição',
            'default_sessions': 'Número Padrão de Sessões',
            'is_active': 'Protocolo Ativo',
        }


class ProtocolSubstanceForm(forms.ModelForm):
    class Meta:
        model = ProtocolSubstance
        fields = ['substance', 'default_quantity', 'is_optional', 'order', 'notes']
        widgets = {
            'substance': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1'
            }),
            'is_optional': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações...'
            }),
        }
        labels = {
            'substance': 'Substância',
            'default_quantity': 'Quantidade Padrão',
            'is_optional': 'Opcional',
            'order': 'Ordem',
            'notes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar substâncias por nome
        self.fields['substance'].queryset = Substance.objects.all().order_by('nome_comum')


# Formset para múltiplas substâncias em um protocolo
ProtocolSubstanceFormSet = inlineformset_factory(
    ProtocolTemplate,
    ProtocolSubstance,
    form=ProtocolSubstanceForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)


class ProtocolSearchForm(forms.Form):
    """Formulário para busca de protocolos."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar protocolos...'
        }),
        label='Buscar'
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('active', 'Ativos'),
            ('inactive', 'Inativos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status'
    )


class DuplicateProtocolForm(forms.Form):
    """Formulário para duplicar protocolo."""
    new_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome do novo protocolo'
        }),
        label='Nome do Novo Protocolo'
    )
    
    copy_description = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Copiar Descrição'
    )


class ProtocolUsageFilterForm(forms.Form):
    """Formulário para filtrar relatório de uso de protocolos."""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Data Inicial'
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Data Final'
    )
    
    unit = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Unidade',
        empty_label='Todas as unidades'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Unit
        self.fields['unit'].queryset = Unit.objects.filter(ativo=True)

