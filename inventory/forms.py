from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date, timedelta

from .models import Substance, Patient


class StockEntryForm(forms.Form):
    """
    Formulário para entrada de estoque.
    """
    substance = forms.ModelChoiceField(
        queryset=Substance.objects.all(),
        label='Substância',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    lote = forms.CharField(
        max_length=100,
        label='Número do Lote',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: LT-2025-001',
            'required': True
        })
    )
    
    quantidade = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        label='Quantidade',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00',
            'required': True
        })
    )
    
    validade = forms.DateField(
        label='Data de Validade',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': date.today().strftime('%Y-%m-%d'),
            'required': True
        })
    )
    
    fornecedor = forms.CharField(
        max_length=200,
        label='Fornecedor',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome do fornecedor',
            'required': True
        })
    )
    
    nota_fiscal_ref = forms.CharField(
        max_length=100,
        required=False,
        label='Referência da Nota Fiscal',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número da NF (opcional)'
        })
    )
    
    preco_unitario = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        validators=[MinValueValidator(Decimal('0'))],
        label='Preço Unitário (R$)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )
    
    motivo = forms.CharField(
        required=False,
        label='Motivo/Observações',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações sobre a entrada (opcional)'
        })
    )


class StockExitForm(forms.Form):
    """
    Formulário para saída de estoque.
    """
    substance = forms.ModelChoiceField(
        queryset=Substance.objects.all(),
        label='Substância',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
            'hx-get': '/inventory/api/substance-stock/',
            'hx-target': '#stock-info',
            'hx-trigger': 'change'
        })
    )
    
    quantidade = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        label='Quantidade',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00',
            'required': True
        })
    )
    
    paciente_nome = forms.CharField(
        max_length=200,
        required=False,
        label='Nome do Paciente',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome do paciente (opcional)'
        })
    )
    
    procedimento = forms.CharField(
        required=False,
        label='Procedimento',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Descrição do procedimento (opcional)'
        })
    )
    
    motivo = forms.CharField(
        required=False,
        label='Motivo/Observações',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo da saída ou observações (opcional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar substâncias por nome
        self.fields['substance'].queryset = Substance.objects.all().order_by('nome_comum')


class QuickStockExitForm(forms.Form):
    """
    Formulário simplificado para saída rápida de estoque.
    """
    substance = forms.ModelChoiceField(
        queryset=Substance.objects.all(),
        label='Substância',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'required': True
        })
    )
    
    quantidade = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        label='Qtd',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00',
            'required': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas substâncias com estoque disponível
        self.fields['substance'].queryset = Substance.objects.filter(
            inventory__quantity_on_hand__gt=0
        ).distinct().order_by('nome_comum')



# Importar formulários de sessões
from .forms_sessions import (
    PatientSessionForm, SessionSubstanceForm, SessionSubstanceFormSet,
    SubstancePriceForm, PaymentUpdateForm, FinancialReportFilterForm
)

