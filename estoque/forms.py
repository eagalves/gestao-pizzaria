from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal

from ingredientes.models import Ingrediente
from .models import Fornecedor, EstoqueIngrediente, CompraIngrediente


class FornecedorForm(forms.ModelForm):
    """Form para cadastro/edição de fornecedores."""
    
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'telefone', 'email', 'endereco', 'observacoes', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do fornecedor'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@fornecedor.com'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o fornecedor'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class EstoqueIngredienteForm(forms.ModelForm):
    """Form para edição de configurações de estoque."""
    
    preco_compra_reais = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        }),
        label='Preço de Compra (R$)'
    )
    
    class Meta:
        model = EstoqueIngrediente
        fields = ['quantidade_atual', 'estoque_minimo', 'estoque_maximo', 'unidade_medida']
        widgets = {
            'quantidade_atual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'estoque_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'unidade_medida': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Preencher preço em reais
            self.fields['preco_compra_reais'].initial = self.instance.preco_compra_atual
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Converter preço de reais para centavos
        preco_reais = self.cleaned_data['preco_compra_reais']
        instance.preco_compra_atual_centavos = int(preco_reais * 100)
        
        if commit:
            instance.save()
            # Recalcular custos dos produtos que usam este ingrediente
            instance._recalcular_custos_produtos()
        
        return instance


class CompraIngredienteForm(forms.ModelForm):
    """Form para registro de compras."""
    
    UNIDADES_CHOICES = [
        ('g', 'Gramas (g)'),
        ('kg', 'Quilos (kg)'),
        ('un', 'Unidade'),
    ]
    
    preco_unitario_reais = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        }),
        label='Preço Unitário (R$)',
        required=False  # Será obrigatório apenas para unidades
    )
    
    unidade = forms.ChoiceField(
        choices=UNIDADES_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Unidade'
    )
    
    valor_total_reais = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        }),
        label='Valor Total (R$)',
        required=False  # Será obrigatório apenas para kg/g
    )
    
    class Meta:
        model = CompraIngrediente
        fields = ['ingrediente', 'fornecedor', 'quantidade', 'unidade', 'data_compra', 'numero_nota', 'observacoes']
        widgets = {
            'ingrediente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fornecedor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'data_compra': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'numero_nota': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da nota fiscal'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre a compra'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        pizzaria = kwargs.pop('pizzaria', None)
        super().__init__(*args, **kwargs)
        
        if pizzaria:
            # Filtrar ingredientes e fornecedores da pizzaria
            self.fields['ingrediente'].queryset = Ingrediente.objects.filter(pizzaria=pizzaria)
            self.fields['fornecedor'].queryset = Fornecedor.objects.filter(pizzaria=pizzaria, ativo=True)
    
    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        unidade = cleaned_data.get('unidade')
        preco_unitario_reais = cleaned_data.get('preco_unitario_reais')
        valor_total_reais = cleaned_data.get('valor_total_reais')
        
        # Regra 1: Para unidades, quantidade deve ser inteiro
        if quantidade and unidade == 'un':
            if quantidade != int(quantidade):
                raise forms.ValidationError({
                    'quantidade': 'Para unidades, a quantidade deve ser um número inteiro.'
                })
        
        # Regra 2: Validações por tipo de unidade
        if unidade == 'un':
            # Para unidades: preço unitário obrigatório, valor total calculado
            if not preco_unitario_reais:
                raise forms.ValidationError({
                    'preco_unitario_reais': 'Preço unitário é obrigatório quando a unidade é "Unidade".'
                })
            if not valor_total_reais:
                raise forms.ValidationError({
                    'valor_total_reais': 'Para unidades, o valor total deveria ser calculado automaticamente.'
                })
        else:
            # Para kg/g: valor total obrigatório, preço unitário não deve ser informado
            if preco_unitario_reais:
                raise forms.ValidationError({
                    'preco_unitario_reais': 'Preço unitário só deve ser informado para unidades.'
                })
            if not valor_total_reais:
                raise forms.ValidationError({
                    'valor_total_reais': 'Valor total é obrigatório para compras em kg/gramas.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Obter dados limpos
        quantidade = self.cleaned_data['quantidade']
        unidade = self.cleaned_data['unidade']
        preco_unitario_reais = self.cleaned_data.get('preco_unitario_reais', 0)
        valor_total_reais = self.cleaned_data.get('valor_total_reais', 0)
        
        if unidade == 'un':
            # Para unidades: calcular valor total automaticamente
            instance.preco_unitario_centavos = int(preco_unitario_reais * 100)
            instance.valor_total_centavos = int(quantidade * instance.preco_unitario_centavos)
        else:
            # Para kg/g: usar valor total informado, calcular preço unitário
            instance.valor_total_centavos = int(valor_total_reais * 100)
            if quantidade > 0:
                instance.preco_unitario_centavos = int(instance.valor_total_centavos / quantidade)
            else:
                instance.preco_unitario_centavos = 0
        
        if commit:
            instance.save()
        
        return instance


class FiltroComprasForm(forms.Form):
    """Form para filtros na lista de compras."""
    
    busca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por ingrediente ou fornecedor...'
        })
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class FiltroEstoqueForm(forms.Form):
    """Form para filtros na lista de estoque."""
    
    FILTRO_CHOICES = [
        ('todos', 'Todos os ingredientes'),
        ('baixo', 'Estoque baixo'),
        ('zerado', 'Estoque zerado'),
    ]
    
    busca = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar ingrediente...'
        })
    )
    
    filtro_estoque = forms.ChoiceField(
        choices=FILTRO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
