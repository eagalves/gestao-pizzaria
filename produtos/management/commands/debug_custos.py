from django.core.management.base import BaseCommand
from produtos.models import Produto


class Command(BaseCommand):
    help = 'Debug detalhado dos custos de produtos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--produto',
            type=int,
            help='ID do produto para debug detalhado',
        )

    def handle(self, *args, **options):
        produto_id = options.get('produto')
        
        if produto_id:
            produtos = Produto.objects.filter(id=produto_id)
        else:
            produtos = Produto.objects.all()
        
        for produto in produtos:
            self.stdout.write(f"\n{'='*50}")
            self.stdout.write(f"PRODUTO: {produto.nome}")
            self.stdout.write(f"{'='*50}")
            
            # Listar ingredientes
            for pi in produto.produto_ingredientes.all():
                ingrediente = pi.ingrediente
                self.stdout.write(f"\n📦 Ingrediente: {ingrediente.nome}")
                self.stdout.write(f"   Quantidade no produto: {pi.quantidade} {pi.get_unidade_display()}")
                
                try:
                    estoque = ingrediente.estoque
                    self.stdout.write(f"   Preço no estoque: R$ {estoque.preco_compra_atual:.2f} por {estoque.get_unidade_medida_display()}")
                    
                    # Testar conversão
                    quantidade_convertida = produto._converter_unidade(
                        pi.quantidade, 
                        pi.unidade, 
                        estoque.unidade_medida
                    )
                    
                    self.stdout.write(f"   Quantidade convertida: {quantidade_convertida} {estoque.get_unidade_medida_display()}")
                    
                    custo_parcial = float(quantidade_convertida) * estoque.preco_compra_atual
                    self.stdout.write(f"   Custo parcial: R$ {custo_parcial:.4f}")
                    
                except Exception as e:
                    self.stdout.write(f"   ❌ ERRO: {e}")
            
            # Total
            self.stdout.write(f"\n💰 CUSTO TOTAL DOS INGREDIENTES: R$ {produto.custo_ingredientes:.2f}")
            
            # Preços do produto
            preco_atual = produto.preco_atual
            if preco_atual:
                self.stdout.write(f"💵 Preço Base: R$ {preco_atual.preco_base:.2f}")
                self.stdout.write(f"💵 Preço Custo: R$ {preco_atual.preco_custo:.2f}")
                self.stdout.write(f"💵 Preço Venda: R$ {preco_atual.preco_venda:.2f}")
                if preco_atual.preco_venda > 0:
                    self.stdout.write(f"📊 Margem: {preco_atual.margem_percentual:.1f}%")
