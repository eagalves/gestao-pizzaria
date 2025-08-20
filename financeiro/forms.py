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
            'observacoes',
            'recorrente',
            'dia_vencimento_recorrente',
            'data_inicio_recorrencia',
            'data_fim_recorrencia'
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
            'recorrente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dia_vencimento_recorrente': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31',
                'placeholder': '1-31'
            }),
            'data_inicio_recorrencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_fim_recorrencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas tipos de despesa ativos
        self.fields['tipo_despesa'].queryset = TipoDespesa.objects.filter(ativo=True)
        
        # Se for uma edição, converter valor de centavos para reais
        if self.instance and self.instance.pk:
            self.fields['valor_reais'].initial = self.instance.valor
        
        # Adicionar classes CSS do Bootstrap para todos os campos
        for field_name, field in self.fields.items():
            if field_name != 'valor_reais' and field_name != 'recorrente':  # valor_reais e recorrente já têm classes
                if isinstance(field.widget, forms.Select):
                    field.widget.attrs['class'] = 'form-select'
                else:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean_valor_reais(self):
        """Converte valor de reais para centavos."""
        valor_reais = self.cleaned_data['valor_reais']
        if valor_reais <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero.")
        return valor_reais
    
    def clean(self):
        """Validações adicionais."""
        cleaned_data = super().clean()
        recorrente = cleaned_data.get('recorrente')
        dia_vencimento_recorrente = cleaned_data.get('dia_vencimento_recorrente')
        data_inicio_recorrencia = cleaned_data.get('data_inicio_recorrencia')
        data_fim_recorrencia = cleaned_data.get('data_fim_recorrencia')
        
        # Se for recorrente, validar campos obrigatórios
        if recorrente:
            if not dia_vencimento_recorrente:
                self.add_error('dia_vencimento_recorrente', 'Dia de vencimento é obrigatório para despesas recorrentes.')
            
            if not data_inicio_recorrencia:
                self.add_error('data_inicio_recorrencia', 'Data de início da recorrência é obrigatória.')
            
            # Validar data de fim se fornecida
            if data_fim_recorrencia and data_inicio_recorrencia and data_fim_recorrencia < data_inicio_recorrencia:
                self.add_error('data_fim_recorrencia', 'A data de fim deve ser posterior à data de início.')
            
            # Validar que o dia de vencimento está entre 1 e 31
            if dia_vencimento_recorrente and (dia_vencimento_recorrente < 1 or dia_vencimento_recorrente > 31):
                self.add_error('dia_vencimento_recorrente', 'O dia de vencimento deve estar entre 1 e 31.')
        
        return cleaned_data
    
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
