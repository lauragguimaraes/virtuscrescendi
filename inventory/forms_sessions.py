from django import forms
from django.forms import inlineformset_factory
from .models import PatientSession, SessionSubstance, Substance
from decimal import Decimal


class PatientSessionForm(forms.ModelForm):
    class Meta:
        model = PatientSession
        fields = [
            'session_date', 'protocol_name', 'procedure_description',
            'clinical_notes', 'payment_status', 'payment_method'
        ]
        widgets = {
            'session_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'protocol_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Protocolo Antioxidante'
            }),
            'procedure_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva o procedimento realizado...'
            }),
            'clinical_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações clínicas...'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class SessionSubstanceForm(forms.ModelForm):
    class Meta:
        model = SessionSubstance
        fields = ['substance', 'quantity', 'unit_price', 'notes']
        widgets = {
            'substance': forms.Select(attrs={
                'class': 'form-select substance-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'step': '0.1',
                'min': '0.1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control price-input',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar substâncias por nome
        self.fields['substance'].queryset = Substance.objects.all().order_by('nome_comum')
        
        # Definir preço padrão se não especificado
        if 'substance' in self.data:
            try:
                substance_id = self.data['substance']
                substance = Substance.objects.get(id=substance_id)
                if not self.data.get('unit_price'):
                    self.fields['unit_price'].initial = substance.preco_padrao
            except (ValueError, Substance.DoesNotExist):
                pass


# Formset para múltiplas substâncias em uma sessão
SessionSubstanceFormSet = inlineformset_factory(
    PatientSession,
    SessionSubstance,
    form=SessionSubstanceForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)


class SubstancePriceForm(forms.ModelForm):
    class Meta:
        model = Substance
        fields = ['preco_padrao']
        widgets = {
            'preco_padrao': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }


class PaymentUpdateForm(forms.ModelForm):
    class Meta:
        model = PatientSession
        fields = ['payment_status', 'payment_method', 'payment_notes']
        widgets = {
            'payment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o pagamento...'
            }),
        }


class FinancialReportFilterForm(forms.Form):
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
    payment_status = forms.ChoiceField(
        choices=[('', 'Todos')] + PatientSession.PAYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status do Pagamento'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Unit
        self.fields['unit'].queryset = Unit.objects.filter(ativo=True)

