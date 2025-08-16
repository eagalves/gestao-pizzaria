from django import forms
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