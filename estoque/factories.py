import factory
from factory.django import DjangoModelFactory
from decimal import Decimal
from datetime import date, timedelta
import random

from autenticacao.models import Pizzaria, UsuarioPizzaria
from ingredientes.models import Ingrediente
from .models import Fornecedor, EstoqueIngrediente, CompraIngrediente, HistoricoPrecoCompra


class PizzariaFactory(DjangoModelFactory):
    """Factory para criação de pizzarias de teste."""
    
    class Meta:
        model = Pizzaria
    
    nome = factory.Faker('company')
    cnpj = factory.Faker('numerify', text='##.###.###/####-##')
    telefone = factory.Faker('numerify', text='(##) #####-####')
    email = factory.Faker('email')
    endereco = factory.Faker('address')
    ativo = True


class UsuarioPizzariaFactory(DjangoModelFactory):
    """Factory para criação de usuários de pizzaria de teste."""
    
    class Meta:
        model = UsuarioPizzaria
    
    usuario = factory.SubFactory('autenticacao.factories.UserFactory')
    pizzaria = factory.SubFactory(PizzariaFactory)
    tipo_usuario = factory.Iterator(['admin', 'gerente', 'funcionario'])


class IngredienteFactory(DjangoModelFactory):
    """Factory para criação de ingredientes de teste."""
    
    class Meta:
        model = Ingrediente
    
    nome = factory.Faker('word')
    descricao = factory.Faker('sentence')
    pizzaria = factory.SubFactory(PizzariaFactory)
    ativo = True


class FornecedorFactory(DjangoModelFactory):
    """Factory para criação de fornecedores de teste."""
    
    class Meta:
        model = Fornecedor
    
    pizzaria = factory.SubFactory(PizzariaFactory)
    nome = factory.Faker('company')
    cnpj = factory.Faker('numerify', text='##.###.###/####-##')
    telefone = factory.Faker('numerify', text='(##) #####-####')
    email = factory.Faker('email')
    endereco = factory.Faker('address')
    observacoes = factory.Faker('paragraph')
    ativo = True


class EstoqueIngredienteFactory(DjangoModelFactory):
    """Factory para criação de estoques de ingredientes de teste."""
    
    class Meta:
        model = EstoqueIngrediente
    
    ingrediente = factory.SubFactory(IngredienteFactory)
    quantidade_atual = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    estoque_minimo = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    estoque_maximo = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    unidade_medida = factory.Iterator(['g', 'kg', 'un'])
    preco_compra_atual_centavos = factory.Faker('pyint', min_value=100, max_value=10000)
    data_ultima_compra = factory.Faker('date_between', start_date='-30d', end_date='today')
    
    @factory.post_generation
    def set_estoque_maximo(self, create, extracted, **kwargs):
        """Garante que estoque_maximo seja maior que estoque_minimo."""
        if create and self.estoque_maximo <= self.estoque_minimo:
            self.estoque_maximo = self.estoque_minimo + Decimal('1.0')
            self.save()


class CompraIngredienteFactory(DjangoModelFactory):
    """Factory para criação de compras de ingredientes de teste."""
    
    class Meta:
        model = CompraIngrediente
    
    ingrediente = factory.SubFactory(IngredienteFactory)
    fornecedor = factory.SubFactory(FornecedorFactory)
    quantidade = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    unidade = factory.Iterator(['g', 'kg', 'un'])
    preco_unitario_centavos = factory.Faker('pyint', min_value=100, max_value=5000)
    data_compra = factory.Faker('date_between', start_date='-30d', end_date='today')
    numero_nota = factory.Faker('numerify', text='NF-######')
    observacoes = factory.Faker('paragraph')
    
    @factory.post_generation
    def set_valor_total(self, create, extracted, **kwargs):
        """Calcula o valor total automaticamente."""
        if create:
            self.valor_total_centavos = int(self.quantidade * self.preco_unitario_centavos)
            self.save()


class HistoricoPrecoCompraFactory(DjangoModelFactory):
    """Factory para criação de histórico de preços de teste."""
    
    class Meta:
        model = HistoricoPrecoCompra
    
    ingrediente = factory.SubFactory(IngredienteFactory)
    preco_centavos = factory.Faker('pyint', min_value=100, max_value=10000)
    data_preco = factory.Faker('date_between', start_date='-90d', end_date='today')
    fornecedor = factory.Faker('company')
    compra = factory.SubFactory(CompraIngredienteFactory)


class EstoqueCompletoFactory:
    """Factory para criar um conjunto completo de dados de estoque."""
    
    @staticmethod
    def create_estoque_completo(pizzaria=None, num_ingredientes=5, num_fornecedores=3):
        """Cria um conjunto completo de dados de estoque para testes."""
        if not pizzaria:
            pizzaria = PizzariaFactory()
        
        # Criar ingredientes
        ingredientes = []
        for i in range(num_ingredientes):
            ingrediente = IngredienteFactory(pizzaria=pizzaria)
            ingredientes.append(ingrediente)
        
        # Criar fornecedores
        fornecedores = []
        for i in range(num_fornecedores):
            fornecedor = FornecedorFactory(pizzaria=pizzaria)
            fornecedores.append(fornecedor)
        
        # Criar estoques
        estoques = []
        for ingrediente in ingredientes:
            estoque = EstoqueIngredienteFactory(ingrediente=ingrediente)
            estoques.append(estoque)
        
        # Criar compras
        compras = []
        for i in range(num_ingredientes * 2):  # 2 compras por ingrediente
            ingrediente = random.choice(ingredientes)
            fornecedor = random.choice(fornecedores)
            compra = CompraIngredienteFactory(
                ingrediente=ingrediente,
                fornecedor=fornecedor
            )
            compras.append(compra)
        
        # Criar histórico de preços
        historicos = []
        for compra in compras:
            historico = HistoricoPrecoCompraFactory(
                ingrediente=compra.ingrediente,
                preco_centavos=compra.preco_unitario_centavos,
                data_preco=compra.data_compra,
                fornecedor=compra.fornecedor.nome if compra.fornecedor else "Não informado",
                compra=compra
            )
            historicos.append(historico)
        
        return {
            'pizzaria': pizzaria,
            'ingredientes': ingredientes,
            'fornecedores': fornecedores,
            'estoques': estoques,
            'compras': compras,
            'historicos': historicos
        }


class EstoqueBaixoFactory:
    """Factory para criar dados de estoque com situação de baixo estoque."""
    
    @staticmethod
    def create_estoque_baixo(pizzaria=None, num_ingredientes=3):
        """Cria ingredientes com estoque baixo para testes."""
        if not pizzaria:
            pizzaria = PizzariaFactory()
        
        ingredientes_baixo = []
        for i in range(num_ingredientes):
            ingrediente = IngredienteFactory(pizzaria=pizzaria)
            estoque = EstoqueIngredienteFactory(
                ingrediente=ingrediente,
                quantidade_atual=Decimal('0.5'),  # Estoque baixo
                estoque_minimo=Decimal('2.0'),    # Mínimo maior que atual
                preco_compra_atual_centavos=2000
            )
            ingredientes_baixo.append({
                'ingrediente': ingrediente,
                'estoque': estoque
            })
        
        return ingredientes_baixo


class EstoqueZeradoFactory:
    """Factory para criar dados de estoque com situação de estoque zerado."""
    
    @staticmethod
    def create_estoque_zerado(pizzaria=None, num_ingredientes=2):
        """Cria ingredientes com estoque zerado para testes."""
        if not pizzaria:
            pizzaria = PizzariaFactory()
        
        ingredientes_zerados = []
        for i in range(num_ingredientes):
            ingrediente = IngredienteFactory(pizzaria=pizzaria)
            estoque = EstoqueIngredienteFactory(
                ingrediente=ingrediente,
                quantidade_atual=Decimal('0.0'),  # Estoque zerado
                estoque_minimo=Decimal('1.0'),    # Mínimo maior que atual
                preco_compra_atual_centavos=1500
            )
            ingredientes_zerados.append({
                'ingrediente': ingrediente,
                'estoque': estoque
            })
        
        return ingredientes_zerados


class CompraRecenteFactory:
    """Factory para criar compras recentes para testes."""
    
    @staticmethod
    def create_compras_recentes(pizzaria=None, num_compras=5, dias_atras=7):
        """Cria compras recentes para testes."""
        if not pizzaria:
            pizzaria = PizzariaFactory()
        
        fornecedor = FornecedorFactory(pizzaria=pizzaria)
        ingrediente = IngredienteFactory(pizzaria=pizzaria)
        
        compras_recentes = []
        for i in range(num_compras):
            data_compra = date.today() - timedelta(days=random.randint(0, dias_atras))
            compra = CompraIngredienteFactory(
                ingrediente=ingrediente,
                fornecedor=fornecedor,
                data_compra=data_compra,
                quantidade=Decimal(random.uniform(1.0, 10.0)),
                preco_unitario_centavos=random.randint(1000, 5000)
            )
            compras_recentes.append(compra)
        
        return compras_recentes


class PrecoVariavelFactory:
    """Factory para criar dados com variação de preços para testes."""
    
    @staticmethod
    def create_precos_variaveis(pizzaria=None, num_ingredientes=3, num_variacoes=5):
        """Cria ingredientes com histórico de variação de preços."""
        if not pizzaria:
            pizzaria = PizzariaFactory()
        
        ingredientes_precos = []
        for i in range(num_ingredientes):
            ingrediente = IngredienteFactory(pizzaria=pizzaria)
            
            # Criar histórico de preços com variações
            historicos = []
            preco_base = random.randint(1000, 3000)
            
            for j in range(num_variacoes):
                # Variação de ±20% no preço
                variacao = random.uniform(0.8, 1.2)
                preco_variado = int(preco_base * variacao)
                
                data_preco = date.today() - timedelta(days=j * 7)  # Uma variação por semana
                
                historico = HistoricoPrecoCompraFactory(
                    ingrediente=ingrediente,
                    preco_centavos=preco_variado,
                    data_preco=data_preco,
                    fornecedor=f"Fornecedor {j+1}"
                )
                historicos.append(historico)
            
            # Criar estoque atual com o preço mais recente
            estoque = EstoqueIngredienteFactory(
                ingrediente=ingrediente,
                preco_compra_atual_centavos=historicos[0].preco_centavos
            )
            
            ingredientes_precos.append({
                'ingrediente': ingrediente,
                'estoque': estoque,
                'historicos': historicos
            })
        
        return ingredientes_precos
