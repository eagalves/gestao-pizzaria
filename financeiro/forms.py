from django import forms
from django.core.validators import MinValueValidator
from .models import DespesaOperacional, TipoDespesa


class DespesaOperacionalForm(forms.ModelForm):
    """Formulário para adicionar/editar despesas operacionais."""
    
    # Campo para valor em reais (mais amigável para o usuário)
    valor_reais = forms.DecimalField(
        label="Valor (R$)",
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        help_text="Digite o valor em reais (ex: 150.50)"
    )
    
    class Meta:
        model = DespesaOperacional
        fields = [
            'tipo_despesa',
            'descricao',
            'tipo',
            'forma_pagamento',
            'data_vencimento',
            'observacoes'
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Aluguel, Luz, Água, etc.'
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais sobre a despesa'
            }),
            'tipo_despesa': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas tipos de despesa ativos
        self.fields['tipo_despesa'].queryset = TipoDespesa.objects.filter(ativo=True)
        
        # Se for uma edição, converter valor de centavos para reais
        if self.instance and self.instance.pk:
            self.fields['valor_reais'].initial = self.instance.valor
    
    def clean_valor_reais(self):
        """Converte valor de reais para centavos."""
        valor_reais = self.cleaned_data['valor_reais']
        if valor_reais <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero.")
        return valor_reais
    
    def save(self, commit=True):
        """Salva a despesa convertendo valor para centavos."""
        despesa = super().save(commit=False)
        
        # Converter valor de reais para centavos
        valor_reais = self.cleaned_data['valor_reais']
        despesa.valor_centavos = int(valor_reais * 100)
        
        if commit:
            despesa.save()
        return despesa


class TipoDespesaForm(forms.ModelForm):
    """Formulário para adicionar/editar tipos de despesa."""
    
    class Meta:
        model = TipoDespesa
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Aluguel, Luz, Água, etc.'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição detalhada do tipo de despesa'
            })
        }
