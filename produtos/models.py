from django.db import models
from django.utils import timezone

from autenticacao.models import Pizzaria
from ingredientes.models import Ingrediente


class CategoriaProduto(models.Model):
    """Categoria (cardápio) pertencente a uma pizzaria."""

    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="categorias_produto",
    )
    nome = models.CharField(max_length=100)
    ordem = models.PositiveIntegerField(default=0, help_text="Ordem de exibição no cardápio")

    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produto"
        unique_together = ("pizzaria", "nome")
        ordering = ("ordem", "nome")

    def __str__(self):
        return self.nome


class Produto(models.Model):
    """Produto que faz parte do cardápio de uma pizzaria."""

    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="produtos",
    )
    categoria = models.ForeignKey(
        CategoriaProduto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produtos",
    )
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    tempo_preparo_minutos = models.PositiveIntegerField(default=15)

    # Flags
    disponivel = models.BooleanField(default=True)
    vegetariano = models.BooleanField(default=False)
    vegano = models.BooleanField(default=False)
    contem_gluten = models.BooleanField(default=False)
    contem_lactose = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        unique_together = ("pizzaria", "nome")
        ordering = ("nome",)

    def __str__(self):
        return f"{self.nome} - {self.pizzaria.nome}"

    @property
    def preco_atual(self):
        """Retorna o preço vigente (data_fim = NULL)."""
        preco = self.precos.filter(data_fim__isnull=True).order_by("-data_inicio").first()
        return preco if preco else None

    @property
    def preco_base_atual(self):
        """Retorna preço base atual em reais."""
        preco = self.preco_atual
        return preco.preco_base if preco else 0

    @property
    def preco_custo_atual(self):
        """Retorna preço de custo atual em reais."""
        preco = self.preco_atual
        return preco.preco_custo if preco else 0

    @property
    def preco_venda_atual(self):
        """Retorna preço de venda atual em reais."""
        preco = self.preco_atual
        return preco.preco_venda if preco else 0

    @property
    def custo_ingredientes_centavos(self):
        """Calcula apenas o custo dos ingredientes em centavos."""
        custo_total_centavos = 0
        
        for produto_ingrediente in self.produto_ingredientes.all():
            ingrediente = produto_ingrediente.ingrediente
            quantidade_produto = produto_ingrediente.quantidade
            unidade_produto = produto_ingrediente.unidade
            
            # Buscar preço atual do ingrediente no estoque
            try:
                estoque = ingrediente.estoque
                preco_por_unidade_estoque_centavos = estoque.preco_compra_atual_centavos
                unidade_estoque = estoque.unidade_medida
                
                # Converter quantidade do produto para a unidade do estoque
                quantidade_convertida = self._converter_unidade(
                    quantidade_produto, 
                    unidade_produto, 
                    unidade_estoque
                )
                
                # Calcular custo: quantidade convertida × preço por unidade
                custo_parcial = int(float(quantidade_convertida) * preco_por_unidade_estoque_centavos)
                custo_total_centavos += custo_parcial
                
            except Exception as e:
                # Se não tem estoque ou erro de conversão, usar 0
                print(f"Erro ao calcular custo do ingrediente {ingrediente.nome}: {e}")
                pass
        
        return custo_total_centavos

    def _converter_unidade(self, quantidade, unidade_origem, unidade_destino):
        """Converte quantidade de uma unidade para outra."""
        if unidade_origem == unidade_destino:
            return quantidade
        
        # Sistema simplificado: apenas kg, g e unidade
        # Unidade NÃO é convertida para gramas - é uma medida independente
        
        # Se uma das unidades é "unidade", só pode converter se ambas forem "unidade"
        if unidade_origem == 'un' or unidade_destino == 'un':
            if unidade_origem == unidade_destino:
                return quantidade
            else:
                # Não é possível converter entre unidade e peso (kg/g)
                raise ValueError(f"Não é possível converter entre {unidade_origem} e {unidade_destino}")
        
        # Conversão apenas entre kg e g
        try:
            if unidade_origem == 'g' and unidade_destino == 'kg':
                return quantidade / 1000  # gramas para kg
            elif unidade_origem == 'kg' and unidade_destino == 'g':
                return quantidade * 1000  # kg para gramas
            else:
                # Se chegou aqui, unidades não suportadas
                raise ValueError(f"Conversão não suportada: {unidade_origem} → {unidade_destino}")
                
        except (KeyError, ZeroDivisionError, ValueError):
            # Se não conseguir converter, lança erro
            raise ValueError(f"Erro na conversão: {unidade_origem} → {unidade_destino}")

    @property
    def custo_ingredientes(self):
        """Retorna custo dos ingredientes em reais."""
        return self.custo_ingredientes_centavos / 100

    def recalcular_custo(self):
        """Recalcula o custo do produto: Preço Base + Custo dos Ingredientes."""
        preco_atual = self.preco_atual
        if preco_atual:
            # Custo = Preço Base + Custo dos Ingredientes
            custo_ingredientes_centavos = self.custo_ingredientes_centavos
            custo_total_centavos = preco_atual.preco_base_centavos + custo_ingredientes_centavos
            
            preco_atual.preco_custo_centavos = custo_total_centavos
            preco_atual.save()
        
        return custo_total_centavos if preco_atual else 0

    def get_ingredientes(self):
        """Retorna todos os ingredientes do produto com suas quantidades."""
        return self.produto_ingredientes.select_related('ingrediente').all()
    
    def get_ingredientes_list(self):
        """Retorna uma lista simples dos nomes dos ingredientes."""
        return [pi.ingrediente.nome for pi in self.produto_ingredientes.all()]


class PrecoProduto(models.Model):
    """Histórico de preços de um produto."""

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="precos",
    )
    
    # Preços em centavos
    preco_base_centavos = models.IntegerField(
        default=0,
        help_text="Preço base em centavos (ex: 3200 = R$ 32,00)"
    )
    preco_custo_centavos = models.IntegerField(
        default=0,
        help_text="Preço de custo em centavos (calculado automaticamente)"
    )
    preco_venda_centavos = models.IntegerField(
        default=0,
        help_text="Preço de venda em centavos (ex: 3550 = R$ 35,50)"
    )
    
    data_inicio = models.DateField(default=timezone.now)
    data_fim = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Preço de Produto"
        verbose_name_plural = "Preços de Produto"
        ordering = ("-data_inicio",)
        constraints = [
            models.UniqueConstraint(
                fields=("produto",),
                condition=models.Q(data_fim__isnull=True),
                name="produto_preco_unico_vigente",
            )
        ]

    def __str__(self):
        return f"{self.produto.nome} - Base: R$ {self.preco_base:.2f} | Venda: R$ {self.preco_venda:.2f} ({self.data_inicio} – {self.data_fim or 'atual'})"

    @property
    def preco_base(self):
        """Retorna preço base em reais."""
        return self.preco_base_centavos / 100

    @property
    def preco_custo(self):
        """Retorna preço de custo em reais."""
        return self.preco_custo_centavos / 100

    @property
    def preco_venda(self):
        """Retorna preço de venda em reais."""
        return self.preco_venda_centavos / 100

    @property
    def margem_percentual(self):
        """Calcula margem percentual sobre o preço de venda."""
        if self.preco_venda_centavos == 0:
            return 0
        return ((self.preco_venda_centavos - self.preco_custo_centavos) / self.preco_venda_centavos) * 100

    @property
    def lucro_centavos(self):
        """Retorna lucro em centavos."""
        return self.preco_venda_centavos - self.preco_custo_centavos

    @property
    def lucro(self):
        """Retorna lucro em reais."""
        return self.lucro_centavos / 100


class ProdutoIngrediente(models.Model):
    """Relação N:M entre Produto e Ingrediente."""

    UNIDADES_CHOICES = [
        ('g', 'Gramas (g)'),
        ('kg', 'Quilos (kg)'),
        ('un', 'Unidade'),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="produto_ingredientes",
    )
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.CASCADE,
        related_name="ingrediente_produtos",
    )
    quantidade = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Quantidade do ingrediente",
    )
    unidade = models.CharField(
        max_length=10,
        choices=UNIDADES_CHOICES,
        default='g',
        help_text="Unidade de medida",
    )

    class Meta:
        verbose_name = "Ingrediente do Produto"
        verbose_name_plural = "Ingredientes do Produto"
        unique_together = ("produto", "ingrediente")

    def __str__(self):
        return f"{self.quantidade} {self.get_unidade_display()} de {self.ingrediente.nome} em {self.produto.nome}"
