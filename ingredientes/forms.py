from django import forms
from .models import Ingrediente

class IngredienteForm(forms.ModelForm):
    """
    Formulário para criar e editar um ingrediente.
    """
    class Meta:
        model = Ingrediente
        fields = [
            'nome', 
            'descricao', 
            'vegetariano', 
            'vegano', 
            'contem_gluten', 
            'contem_lactose'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vegetariano': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vegano': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contem_gluten': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contem_lactose': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
