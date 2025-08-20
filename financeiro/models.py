from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

from autenticacao.models import Pizzaria


class TipoDespesa(models.Model):
    """Tipos de despesas operacionais."""
    
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tipo de Despesa"
        verbose_name_plural = "Tipos de Despesa"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class DespesaOperacional(models.Model):
    """Despesas operacionais da pizzaria."""
    
    TIPO_DESPESA_CHOICES = [
        ('FIXA', 'Despesa Fixa'),
        ('VARIAVEL', 'Despesa Variável'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('DIN', 'Dinheiro'),
        ('PIX', 'Pix'),
        ('TED', 'TED/DOC'),
        ('CC', 'Cartão Crédito'),
        ('CD', 'Cartão Débito'),
        ('BOL', 'Boleto'),
        ('DEB', 'Débito Automático'),
    ]
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="despesas"
    )
    tipo_despesa = models.ForeignKey(
        TipoDespesa,
        on_delete=models.PROTECT,
        related_name="despesas"
    )
    descricao = models.CharField(max_length=200)
    
    # Valor em centavos
    valor_centavos = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Valor em centavos (ex: 15000 = R$ 150,00)"
    )
    
    tipo = models.CharField(max_length=10, choices=TIPO_DESPESA_CHOICES)
    forma_pagamento = models.CharField(max_length=3, choices=FORMA_PAGAMENTO_CHOICES)
    
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    
    pago = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Despesa Operacional"
        verbose_name_plural = "Despesas Operacionais"
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor:.2f} ({self.data_vencimento})"
    
    @property
    def valor(self):
        """Retorna valor em reais."""
        return self.valor_centavos / 100
    
    @property
    def em_atraso(self):
        """Verifica se a despesa está em atraso."""
        if self.pago:
            return False
        return self.data_vencimento < timezone.now().date()
    
    def marcar_como_paga(self, data_pagamento=None):
        """Marca despesa como paga."""
        self.pago = True
        self.data_pagamento = data_pagamento or timezone.now().date()
        self.save()


class MovimentacaoCaixa(models.Model):
    """Controle de entradas e saídas do caixa."""
    
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]
    
    ORIGEM_CHOICES = [
        ('VENDA', 'Venda (Pedido)'),
        ('DESPESA', 'Despesa Operacional'),
        ('COMPRA', 'Compra de Estoque'),
        ('AJUSTE', 'Ajuste Manual'),
        ('OUTROS', 'Outros'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('DIN', 'Dinheiro'),
        ('PIX', 'Pix'),
        ('TED', 'TED/DOC'),
        ('CC', 'Cartão Crédito'),
        ('CD', 'Cartão Débito'),
        ('BOL', 'Boleto'),
        ('DEB', 'Débito Automático'),
    ]
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="movimentacoes_caixa"
    )
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    origem = models.CharField(max_length=10, choices=ORIGEM_CHOICES)
    descricao = models.CharField(max_length=200)
    
    # Valor em centavos
    valor_centavos = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Valor em centavos (ex: 5500 = R$ 55,00)"
    )
    
    forma_pagamento = models.CharField(max_length=3, choices=FORMA_PAGAMENTO_CHOICES)
    data_movimentacao = models.DateTimeField(default=timezone.now)
    
    # Referências opcionais
    pedido = models.ForeignKey(
        'pedidos.Pedido',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes"
    )
    despesa = models.ForeignKey(
        DespesaOperacional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes"
    )
    compra_estoque = models.ForeignKey(
        'estoque.CompraIngrediente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes"
    )
    
    observacoes = models.TextField(blank=True)
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Movimentação de Caixa"
        verbose_name_plural = "Movimentações de Caixa"
        ordering = ['-data_movimentacao']
    
    def __str__(self):
        sinal = '+' if self.tipo == 'ENTRADA' else '-'
        return f"{sinal}R$ {self.valor:.2f} - {self.descricao} ({self.data_movimentacao.strftime('%d/%m/%Y')})"
    
    @property
    def valor(self):
        """Retorna valor em reais."""
        return self.valor_centavos / 100
    
    @property
    def valor_com_sinal(self):
        """Retorna valor com sinal (+ para entrada, - para saída)."""
        valor = self.valor
        return valor if self.tipo == 'ENTRADA' else -valor


class MetaVenda(models.Model):
    """Metas de vendas mensais."""
    
    TIPO_META_CHOICES = [
        ('RECEITA', 'Meta de Receita'),
        ('QUANTIDADE', 'Meta de Quantidade'),
        ('TICKET', 'Meta de Ticket Médio'),
    ]
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="metas_vendas"
    )
    
    nome = models.CharField(max_length=100)
    tipo_meta = models.CharField(max_length=12, choices=TIPO_META_CHOICES)
    
    # Valores das metas
    meta_receita_centavos = models.IntegerField(
        default=0,
        help_text="Meta de receita em centavos"
    )
    meta_quantidade = models.IntegerField(
        default=0,
        help_text="Meta de quantidade de pedidos"
    )
    meta_ticket_medio_centavos = models.IntegerField(
        default=0,
        help_text="Meta de ticket médio em centavos"
    )
    
    # Período
    mes = models.IntegerField(validators=[MinValueValidator(1), MinValueValidator(12)])
    ano = models.IntegerField(validators=[MinValueValidator(2020)])
    
    # Categoria específica (opcional)
    categoria = models.ForeignKey(
        'produtos.CategoriaProduto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="metas"
    )
    
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meta de Venda"
        verbose_name_plural = "Metas de Vendas"
        unique_together = ('pizzaria', 'nome', 'mes', 'ano')
        ordering = ['-ano', '-mes']
    
    def __str__(self):
        categoria_str = f" - {self.categoria.nome}" if self.categoria else ""
        return f"{self.nome} ({self.mes:02d}/{self.ano}){categoria_str}"
    
    @property
    def meta_receita(self):
        """Retorna meta de receita em reais."""
        return self.meta_receita_centavos / 100
    
    @property
    def meta_ticket_medio(self):
        """Retorna meta de ticket médio em reais."""
        return self.meta_ticket_medio_centavos / 100
