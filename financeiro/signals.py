from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from pedidos.models import Pedido
from estoque.models import CompraIngrediente
from .models import DespesaOperacional, MovimentacaoCaixa


@receiver(post_save, sender=Pedido)
def criar_movimentacao_venda(sender, instance, created, **kwargs):
    """Cria movimentação de entrada quando um pedido é entregue."""
    if instance.status == 'ENTREGUE':
        # Verificar se já existe movimentação para este pedido
        if not MovimentacaoCaixa.objects.filter(pedido=instance).exists():
            # Converter total para centavos
            valor_centavos = int(float(instance.total) * 100)
            
            MovimentacaoCaixa.objects.create(
                pizzaria=instance.pizzaria,
                tipo='ENTRADA',
                origem='VENDA',
                descricao=f'Venda - Pedido #{instance.id}',
                valor_centavos=valor_centavos,
                forma_pagamento=instance.forma_pagamento,
                data_movimentacao=instance.data_criacao,
                pedido=instance
            )


@receiver(post_save, sender=CompraIngrediente)
def criar_movimentacao_compra(sender, instance, created, **kwargs):
    """Cria movimentação de saída quando uma compra de estoque é registrada."""
    if created:  # Só criar quando for uma nova compra
        # Verificar se já existe movimentação para esta compra
        if not MovimentacaoCaixa.objects.filter(compra_estoque=instance).exists():
            # Usar timezone.now() para evitar warning de timezone
            data_movimentacao = timezone.now().replace(
                year=instance.data_compra.year,
                month=instance.data_compra.month,
                day=instance.data_compra.day
            )
            
            MovimentacaoCaixa.objects.create(
                pizzaria=instance.ingrediente.pizzaria,
                tipo='SAIDA',
                origem='COMPRA',
                descricao=f'Compra - {instance.ingrediente.nome} ({instance.fornecedor.nome if instance.fornecedor else "Fornecedor não informado"})',
                valor_centavos=instance.valor_total_centavos,
                forma_pagamento='DIN',  # Padrão, pode ser ajustado depois
                data_movimentacao=data_movimentacao,
                compra_estoque=instance
            )


@receiver(post_save, sender=DespesaOperacional)
def criar_movimentacao_despesa(sender, instance, created, **kwargs):
    """Cria movimentação de saída quando uma despesa é marcada como paga."""
    if instance.pago and instance.data_pagamento:
        # Verificar se já existe movimentação para esta despesa
        if not MovimentacaoCaixa.objects.filter(despesa=instance).exists():
            # Usar timezone.now() para evitar warning de timezone
            data_movimentacao = timezone.now().replace(
                year=instance.data_pagamento.year,
                month=instance.data_pagamento.month,
                day=instance.data_pagamento.day
            )
            
            MovimentacaoCaixa.objects.create(
                pizzaria=instance.pizzaria,
                tipo='SAIDA',
                origem='DESPESA',
                descricao=f'Despesa - {instance.descricao}',
                valor_centavos=instance.valor_centavos,
                forma_pagamento=instance.forma_pagamento,
                data_movimentacao=data_movimentacao,
                despesa=instance
            )


@receiver(post_delete, sender=Pedido)
def remover_movimentacao_venda(sender, instance, **kwargs):
    """Remove movimentação quando um pedido é excluído."""
    MovimentacaoCaixa.objects.filter(pedido=instance).delete()


@receiver(post_delete, sender=CompraIngrediente)
def remover_movimentacao_compra(sender, instance, **kwargs):
    """Remove movimentação quando uma compra é excluída."""
    MovimentacaoCaixa.objects.filter(compra_estoque=instance).delete()


@receiver(post_delete, sender=DespesaOperacional)
def remover_movimentacao_despesa(sender, instance, **kwargs):
    """Remove movimentação quando uma despesa é excluída."""
    MovimentacaoCaixa.objects.filter(despesa=instance).delete()
