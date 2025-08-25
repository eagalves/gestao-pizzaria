from django import forms
from .models import Pedido, ItemPedido


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['cliente', 'cliente_nome', 'cliente_telefone', 'observacoes', 'forma_pagamento', 'status']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'cliente_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ItemPedidoForm(forms.ModelForm):
    class Meta:
        model = ItemPedido
        fields = ['produto', 'quantidade', 'valor_unitario', 'observacao_item']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacao_item': forms.TextInput(attrs={'class': 'form-control'}),
        }
