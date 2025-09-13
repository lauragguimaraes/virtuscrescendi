from django import forms
from .models import TransferNew, TransferItemNew, Unit, Substance

class TransferForm(forms.ModelForm):
    class Meta:
        model = TransferNew
        fields = ['unidade_origem', 'unidade_destino', 'observacoes']
        widgets = {
            'unidade_origem': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'unidade_destino': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a transferência...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unidade_origem'].queryset = Unit.objects.filter(ativo=True)
        self.fields['unidade_destino'].queryset = Unit.objects.filter(ativo=True)

class TransferItemForm(forms.ModelForm):
    class Meta:
        model = TransferItemNew
        fields = ['substance', 'quantidade', 'observacoes']
        widgets = {
            'substance': forms.Select(attrs={
                'class': 'form-control substance-select',
                'required': True
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '0.01',
                'step': '0.01',
                'required': True
            }),
            'observacoes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Observações do item...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['substance'].queryset = Substance.objects.all().order_by('nome_comum')

