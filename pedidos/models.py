from django.db import models
from django.utils import timezone

from autenticacao.models import Pizzaria
from produtos.models import Produto


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("RASCUNHO", "Rascunho"),
        ("RECEBIDO", "Recebido"),
        ("EM_PREPARO", "Em Preparo"),
        ("PRONTO", "Pronto"),
        ("ENTREGUE", "Entregue"),
        ("CANCELADO", "Cancelado"),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ("DIN", "Dinheiro"),
        ("PIX", "Pix"),
        ("CC", "Cartão Crédito"),
        ("CD", "Cartão Débito"),
    ]

    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    
    # Relacionamento com Cliente (opcional - para pedidos de balcão)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos"
    )
    
    # Campos para pedidos sem cadastro de cliente (balcão/telefone)
    cliente_nome = models.CharField(max_length=120, blank=True)
    cliente_telefone = models.CharField(max_length=20, blank=True)
    observacoes = models.CharField(max_length=255, blank=True)

    forma_pagamento = models.CharField(max_length=3, choices=FORMA_PAGAMENTO_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="RECEBIDO")

    total = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    data_criacao = models.DateTimeField(default=timezone.now)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-data_criacao",)

    def __str__(self):
        return f"Pedido #{self.id} - {self.pizzaria.nome}"

    def atualizar_total(self):
        soma = sum(item.subtotal for item in self.itens.all())
        self.total = soma
        self.save(update_fields=["total"])
    
    def get_cliente_nome(self):
        """Retorna o nome do cliente (cadastrado ou informado)"""
        if self.cliente:
            return self.cliente.nome
        return self.cliente_nome or "Cliente não informado"
    
    def get_cliente_telefone(self):
        """Retorna o telefone do cliente (cadastrado ou informado)"""
        if self.cliente:
            return self.cliente.telefone
        return self.cliente_telefone or ""


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)
    valor_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    observacao_item = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    @property
    def subtotal(self):
        return self.valor_unitario * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Pedido {self.pedido.id})"
