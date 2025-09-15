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

    # Flag para controlar se o estoque já foi abatido para este pedido
    estoque_baixado = models.BooleanField(default=False)

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

    # --------------------------------------------------
    # Estoque
    # --------------------------------------------------

    def _converter_unidade(self, quantidade, unidade_origem, unidade_destino):
        """Converte quantidade entre g, kg e un.

        A lógica é similar à utilizada em Produto/ProdutoIngrediente.
        """
        if unidade_origem == unidade_destino:
            return quantidade

        # Caso envolva unidade de peça não convertível
        if unidade_origem == 'un' or unidade_destino == 'un':
            raise ValueError("Não é possível converter entre unidade e peso.")

        if unidade_origem == 'g' and unidade_destino == 'kg':
            return quantidade / 1000
        if unidade_origem == 'kg' and unidade_destino == 'g':
            return quantidade * 1000

        raise ValueError(f"Conversão não suportada: {unidade_origem} → {unidade_destino}")

    def _baixar_estoque(self):
        """Abate os ingredientes usados neste pedido do estoque."""
        from estoque.models import EstoqueIngrediente  # import local para evitar ciclos

        for item in self.itens.select_related('produto').all():
            produto = item.produto

            # Percorrer ingredientes do produto
            for prod_ing in produto.produto_ingredientes.select_related('ingrediente').all():
                ingrediente = prod_ing.ingrediente

                # Quantidade total necessária = quantidade por produto × quantidade de itens
                quantidade_necessaria = prod_ing.quantidade * item.quantidade

                try:
                    estoque = ingrediente.estoque
                except EstoqueIngrediente.DoesNotExist:
                    # Se não houver estoque, simplesmente continuar
                    continue

                # Converter para unidade do estoque
                try:
                    quantidade_convertida = self._converter_unidade(
                        quantidade_necessaria,
                        prod_ing.unidade,
                        estoque.unidade_medida,
                    )
                except Exception:
                    # Se não conseguir converter, ignora este ingrediente
                    continue

                # Subtrair do estoque
                estoque_antes = estoque.quantidade_atual
                estoque.quantidade_atual = max(0, estoque.quantidade_atual - quantidade_convertida)
                estoque.save(update_fields=["quantidade_atual", "data_atualizacao"])

                # Registrar histórico de uso
                from estoque.models import HistoricoUsoIngrediente

                HistoricoUsoIngrediente.objects.create(
                    ingrediente=ingrediente,
                    pedido=self,
                    quantidade=quantidade_convertida,
                    unidade=estoque.unidade_medida,
                    estoque_antes=estoque_antes,
                    estoque_depois=estoque.quantidade_atual,
                )

    def save(self, *args, **kwargs):
        """Sobrescreve save para realizar baixa de estoque ao mudar status."""
        # Verificar se o objeto já existe para detectar mudança de status
        if self.pk:
            original = Pedido.objects.get(pk=self.pk)
            status_anterior = original.status
        else:
            status_anterior = None

        super().save(*args, **kwargs)

        # Se status mudou para PRONTO ou ENTREGUE e estoque ainda não foi baixado
        if (
            self.status in {"PRONTO", "ENTREGUE"}
            and not self.estoque_baixado
        ):
            # Garantir que não corra mais de uma vez
            self._baixar_estoque()
            self.estoque_baixado = True
            super().save(update_fields=["estoque_baixado"])
    
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
