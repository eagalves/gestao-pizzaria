from django import forms
from .models import Pizzaria


class PizzariaForm(forms.ModelForm):
    class Meta:
        model = Pizzaria
        fields = ['nome', 'cnpj', 'telefone', 'endereco', 'ativa']
        labels = {
            'nome': 'Nome da Pizzaria',
            'cnpj': 'CNPJ',
            'telefone': 'Telefone',
            'endereco': 'Endereço',
            'ativa': 'Ativa',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }