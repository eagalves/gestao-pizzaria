from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from django.utils import timezone

from pedidos.models import Pedido
from estoque.models import CompraIngrediente
from financeiro.models import MovimentacaoCaixa


class Command(BaseCommand):
    help = 'Integra pedidos entregues e compras de estoque como movimentações financeiras'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove todas as movimentações automáticas antes de recriar',
        )
        parser.add_argument(
            '--data-inicio',
            type=str,
            help='Data de início no formato YYYY-MM-DD',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando integração das movimentações financeiras...'))
        
        if options['limpar']:
            self.limpar_movimentacoes_automaticas()
        
        data_inicio = options.get('data_inicio')
        if data_inicio:
            try:
                data_inicio = timezone.datetime.strptime(data_inicio, '%Y-%m-%d').date()
                self.stdout.write(f'Processando dados a partir de: {data_inicio}')
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Formato de data inválido. Use YYYY-MM-DD')
                )
                return
        
        with transaction.atomic():
            entradas_criadas = self.criar_movimentacoes_vendas(data_inicio)
            saidas_criadas = self.criar_movimentacoes_compras(data_inicio)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Integração concluída!\n'
                f'- {entradas_criadas} entradas criadas (vendas)\n'
                f'- {saidas_criadas} saídas criadas (compras)'
            )
        )

    def limpar_movimentacoes_automaticas(self):
        """Remove movimentações criadas automaticamente."""
        self.stdout.write('Removendo movimentações automáticas existentes...')
        
        # Remove movimentações que têm referência a pedido ou compra
        movimentacoes_removidas = MovimentacaoCaixa.objects.filter(
            models.Q(pedido__isnull=False) | models.Q(compra_estoque__isnull=False)
        ).count()
        
        MovimentacaoCaixa.objects.filter(
            models.Q(pedido__isnull=False) | models.Q(compra_estoque__isnull=False)
        ).delete()
        
        self.stdout.write(f'Removidas {movimentacoes_removidas} movimentações automáticas.')

    def criar_movimentacoes_vendas(self, data_inicio=None):
        """Cria movimentações de entrada para pedidos entregues."""
        self.stdout.write('Criando movimentações para vendas (pedidos entregues)...')
        
        # Buscar pedidos entregues que ainda não têm movimentação
        pedidos_query = Pedido.objects.filter(
            status='ENTREGUE',
            movimentacoes__isnull=True  # Que não têm movimentação associada
        )
        
        if data_inicio:
            pedidos_query = pedidos_query.filter(data_criacao__date__gte=data_inicio)
        
        pedidos = pedidos_query.select_related('pizzaria')
        
        movimentacoes_criadas = []
        for pedido in pedidos:
            # Converter total do pedido para centavos
            valor_centavos = int(float(pedido.total) * 100)
            
            movimentacao = MovimentacaoCaixa(
                pizzaria=pedido.pizzaria,
                tipo='ENTRADA',
                origem='VENDA',
                descricao=f'Venda - Pedido #{pedido.id}',
                valor_centavos=valor_centavos,
                forma_pagamento=pedido.forma_pagamento,
                data_movimentacao=pedido.data_criacao,
                pedido=pedido
            )
            movimentacoes_criadas.append(movimentacao)
        
        # Criar em lote para melhor performance
        MovimentacaoCaixa.objects.bulk_create(movimentacoes_criadas)
        
        self.stdout.write(f'Criadas {len(movimentacoes_criadas)} movimentações de entrada.')
        return len(movimentacoes_criadas)

    def criar_movimentacoes_compras(self, data_inicio=None):
        """Cria movimentações de saída para compras de estoque."""
        self.stdout.write('Criando movimentações para compras de estoque...')
        
        # Buscar compras que ainda não têm movimentação
        compras_query = CompraIngrediente.objects.filter(
            movimentacoes__isnull=True  # Que não têm movimentação associada
        )
        
        if data_inicio:
            compras_query = compras_query.filter(data_compra__gte=data_inicio)
        
        compras = compras_query.select_related('ingrediente__pizzaria', 'fornecedor')
        
        movimentacoes_criadas = []
        for compra in compras:
            movimentacao = MovimentacaoCaixa(
                pizzaria=compra.ingrediente.pizzaria,
                tipo='SAIDA',
                origem='COMPRA',
                descricao=f'Compra - {compra.ingrediente.nome} ({compra.fornecedor.nome if compra.fornecedor else "Fornecedor não informado"})',
                valor_centavos=compra.valor_total_centavos,
                forma_pagamento='DIN',  # Padrão, pode ser ajustado depois
                data_movimentacao=timezone.datetime.combine(
                    compra.data_compra, 
                    timezone.now().time()
                ),
                compra_estoque=compra
            )
            movimentacoes_criadas.append(movimentacao)
        
        # Criar em lote para melhor performance
        MovimentacaoCaixa.objects.bulk_create(movimentacoes_criadas)
        
        self.stdout.write(f'Criadas {len(movimentacoes_criadas)} movimentações de saída.')
        return len(movimentacoes_criadas)
