from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Produto, PrecoProduto, CategoriaProduto, ProdutoIngrediente
from ingredientes.models import Ingrediente

class ProdutoForm(forms.ModelForm):
    preco_base = forms.DecimalField(label="Preço Base (R$)", max_digits=8, decimal_places=2)

    class Meta:
        model = Produto
        fields = [
            'categoria',
            'nome',
            'descricao',
            'tempo_preparo_minutos',
            'disponivel',
            'vegetariano',
            'vegano',
            'contem_gluten',
            'contem_lactose',
        ]
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tempo_preparo_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'disponivel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vegetariano': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vegano': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contem_gluten': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contem_lactose': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        pizzaria = kwargs.pop('pizzaria', None)
        super().__init__(*args, **kwargs)
        if pizzaria:
            self.fields['categoria'].queryset = CategoriaProduto.objects.filter(pizzaria=pizzaria)


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = ['nome', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Pizzas Tradicionais'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            })
        }
        labels = {
            'nome': 'Nome da Categoria',
            'ordem': 'Ordem de Exibição'
        }
        help_texts = {
            'ordem': 'Menor número aparece primeiro no cardápio'
        }


class PrecoProdutoForm(forms.ModelForm):
    """Form para gerenciar preços de produtos."""
    
    preco_base_reais = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        }),
        label='Preço Base (R$)',
        help_text='Preço base do produto (sem considerar ingredientes)'
    )
    
    preco_venda_reais = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0,00'
        }),
        label='Preço de Venda (R$)',
        help_text='Preço final que será cobrado do cliente'
    )

    class Meta:
        model = PrecoProduto
        fields = []  # Não incluímos campos do model diretamente

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Preencher preços em reais
            self.fields['preco_base_reais'].initial = self.instance.preco_base
            self.fields['preco_venda_reais'].initial = self.instance.preco_venda

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Converter preços de reais para centavos
        preco_base_reais = self.cleaned_data['preco_base_reais']
        preco_venda_reais = self.cleaned_data['preco_venda_reais']
        
        instance.preco_base_centavos = int(preco_base_reais * 100)
        instance.preco_venda_centavos = int(preco_venda_reais * 100)
        
        if commit:
            instance.save()
            # Recalcular custo após salvar
            instance.produto.recalcular_custo()
        
        return instance