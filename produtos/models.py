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
        return f"{self.nome} - {self.pizzaria.nome}"


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
        return preco.valor if preco else 0

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
    valor = models.DecimalField(max_digits=8, decimal_places=2)
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
        return f"{self.produto.nome} - R$ {self.valor} ({self.data_inicio} – {self.data_fim or 'atual'})"


class ProdutoIngrediente(models.Model):
    """Relação N:M entre Produto e Ingrediente."""

    UNIDADES_CHOICES = [
        ('g', 'Gramas (g)'),
        ('kg', 'Quilos (kg)'),
        ('ml', 'Mililitros (ml)'),
        ('l', 'Litros (l)'),
        ('un', 'Unidade'),
        ('fatia', 'Fatia'),
        ('pitada', 'Pitada'),
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
