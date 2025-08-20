from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from financeiro.models import MovimentacaoCaixa
from pedidos.models import Pedido
from estoque.models import CompraIngrediente
from financeiro.models import DespesaOperacional


class Command(BaseCommand):
    help = 'Verifica o status das movimentações financeiras'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== VERIFICAÇÃO DAS MOVIMENTAÇÕES FINANCEIRAS ==='))
        
        # Contar movimentações existentes
        total_movimentacoes = MovimentacaoCaixa.objects.count()
        entradas = MovimentacaoCaixa.objects.filter(tipo='ENTRADA').count()
        saidas = MovimentacaoCaixa.objects.filter(tipo='SAIDA').count()
        
        self.stdout.write(f'\n📊 MOVIMENTAÇÕES EXISTENTES:')
        self.stdout.write(f'   Total: {total_movimentacoes}')
        self.stdout.write(f'   Entradas: {entradas}')
        self.stdout.write(f'   Saídas: {saidas}')
        
        # Verificar pedidos entregues
        pedidos_entregues = Pedido.objects.filter(status='ENTREGUE').count()
        pedidos_com_movimentacao = Pedido.objects.filter(
            status='ENTREGUE',
            movimentacoes__isnull=False
        ).count()
        
        self.stdout.write(f'\n🛒 PEDIDOS ENTREGUES:')
        self.stdout.write(f'   Total entregues: {pedidos_entregues}')
        self.stdout.write(f'   Com movimentação: {pedidos_com_movimentacao}')
        self.stdout.write(f'   Sem movimentação: {pedidos_entregues - pedidos_com_movimentacao}')
        
        # Verificar compras de estoque
        compras_estoque = CompraIngrediente.objects.count()
        compras_com_movimentacao = CompraIngrediente.objects.filter(
            movimentacoes__isnull=False
        ).count()
        
        self.stdout.write(f'\n📦 COMPRAS DE ESTOQUE:')
        self.stdout.write(f'   Total compras: {compras_estoque}')
        self.stdout.write(f'   Com movimentação: {compras_com_movimentacao}')
        self.stdout.write(f'   Sem movimentação: {compras_estoque - compras_com_movimentacao}')
        
        # Verificar despesas pagas
        despesas_pagas = DespesaOperacional.objects.filter(pago=True).count()
        despesas_com_movimentacao = DespesaOperacional.objects.filter(
            pago=True,
            movimentacoes__isnull=False
        ).count()
        
        self.stdout.write(f'\n💰 DESPESAS PAGAS:')
        self.stdout.write(f'   Total pagas: {despesas_pagas}')
        self.stdout.write(f'   Com movimentação: {despesas_com_movimentacao}')
        self.stdout.write(f'   Sem movimentação: {despesas_pagas - despesas_com_movimentacao}')
        
        # Resumo
        self.stdout.write(f'\n📋 RESUMO:')
        if pedidos_entregues == pedidos_com_movimentacao and compras_estoque == compras_com_movimentacao:
            self.stdout.write(self.style.SUCCESS('✅ Todas as movimentações estão sincronizadas!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Existem registros sem movimentações correspondentes.'))
            self.stdout.write(self.style.INFO('💡 Execute: python manage.py integrar_movimentacoes_financeiras'))
        
        # Mostrar algumas movimentações recentes
        self.stdout.write(f'\n🕒 MOVIMENTAÇÕES RECENTES:')
        movimentacoes_recentes = MovimentacaoCaixa.objects.order_by('-data_movimentacao')[:5]
        for mov in movimentacoes_recentes:
            sinal = '+' if mov.tipo == 'ENTRADA' else '-'
            self.stdout.write(f'   {sinal}R$ {mov.valor:.2f} - {mov.descricao} ({mov.data_movimentacao.strftime("%d/%m/%Y %H:%M")})')
