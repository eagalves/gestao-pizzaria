from django.core.management.base import BaseCommand
from django.utils import timezone
from produtos.models import Produto, PrecoProduto


class Command(BaseCommand):
    help = 'Recalcula os custos de todos os produtos baseado nos ingredientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pizzaria',
            type=int,
            help='ID da pizzaria para recalcular (opcional, se não informado recalcula todas)',
        )

    def handle(self, *args, **options):
        pizzaria_id = options.get('pizzaria')
        
        if pizzaria_id:
            produtos = Produto.objects.filter(pizzaria_id=pizzaria_id)
            self.stdout.write(f'Recalculando custos para pizzaria ID {pizzaria_id}...')
        else:
            produtos = Produto.objects.all()
            self.stdout.write('Recalculando custos para todas as pizzarias...')
        
        produtos_atualizados = 0
        produtos_sem_preco = 0
        
        for produto in produtos:
            try:
                # Verificar se o produto tem preço atual
                preco_atual = produto.preco_atual
                
                if not preco_atual:
                    # Criar preço inicial se não existir
                    PrecoProduto.objects.create(
                        produto=produto,
                        preco_base_centavos=0,
                        preco_custo_centavos=0,
                        preco_venda_centavos=0,
                        data_inicio=timezone.now().date()
                    )
                    produtos_sem_preco += 1
                    self.stdout.write(
                        self.style.WARNING(f'Criado preço inicial para: {produto.nome}')
                    )
                
                # Recalcular custo
                produto.recalcular_custo()
                produtos_atualizados += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {produto.nome} - Custo: R$ {produto.preco_custo_atual:.2f}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Erro ao processar {produto.nome}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nResumo:\n'
                f'- Produtos atualizados: {produtos_atualizados}\n'
                f'- Produtos sem preço (criados): {produtos_sem_preco}\n'
                f'- Total processado: {produtos.count()}'
            )
        )
