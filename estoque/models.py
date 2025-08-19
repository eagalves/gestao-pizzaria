from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

from autenticacao.models import Pizzaria
from ingredientes.models import Ingrediente


class Fornecedor(models.Model):
    """Fornecedores de ingredientes para cada pizzaria."""
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="fornecedores"
    )
    nome = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=18, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        unique_together = ('pizzaria', 'nome')
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.pizzaria.nome}"


class EstoqueIngrediente(models.Model):
    """Controle de estoque para cada ingrediente."""
    
    UNIDADES_CHOICES = [
        ('g', 'Gramas (g)'),
        ('kg', 'Quilos (kg)'),
        ('un', 'Unidade'),
    ]
    
    ingrediente = models.OneToOneField(
        Ingrediente,
        on_delete=models.CASCADE,
        related_name="estoque"
    )
    quantidade_atual = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    estoque_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    estoque_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    unidade_medida = models.CharField(
        max_length=10,
        choices=UNIDADES_CHOICES,
        default='kg'
    )
    
    # Preço atual em centavos
    preco_compra_atual_centavos = models.IntegerField(
        default=0,
        help_text="Preço em centavos (ex: 2550 = R$ 25,50)"
    )
    
    data_ultima_compra = models.DateField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estoque de Ingrediente"
        verbose_name_plural = "Estoque de Ingredientes"

    def __str__(self):
        return f"{self.ingrediente.nome} - {self.quantidade_atual} {self.get_unidade_medida_display()}"

    @property
    def preco_compra_atual(self):
        """Retorna preço em reais."""
        return self.preco_compra_atual_centavos / 100

    @property
    def estoque_baixo(self):
        """Verifica se o estoque está abaixo do mínimo."""
        return self.quantidade_atual <= self.estoque_minimo

    @property
    def valor_total_estoque(self):
        """Valor total do estoque atual em reais."""
        return (self.quantidade_atual * self.preco_compra_atual_centavos) / 100

    def atualizar_preco(self, novo_preco_centavos):
        """Atualiza o preço atual e recalcula custos dos produtos."""
        self.preco_compra_atual_centavos = novo_preco_centavos
        self.save()
        
        # Recalcular custo de todos os produtos que usam este ingrediente
        self._recalcular_custos_produtos()

    def _recalcular_custos_produtos(self):
        """Recalcula o custo de todos os produtos que usam este ingrediente."""
        from produtos.models import Produto
        
        produtos_afetados = Produto.objects.filter(
            produto_ingredientes__ingrediente=self.ingrediente
        ).distinct()
        
        for produto in produtos_afetados:
            produto.recalcular_custo()


class CompraIngrediente(models.Model):
    """Registro de compras de ingredientes."""
    
    UNIDADES_CHOICES = [
        ('g', 'Gramas (g)'),
        ('kg', 'Quilos (kg)'),
        ('un', 'Unidade'),
    ]
    
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.CASCADE,
        related_name="compras"
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0.001)]
    )
    unidade = models.CharField(
        max_length=10,
        choices=UNIDADES_CHOICES,
        default='kg',
        help_text="Unidade da quantidade comprada"
    )
    
    # Preço unitário em centavos
    preco_unitario_centavos = models.IntegerField(
        help_text="Preço por unidade em centavos (ex: 2550 = R$ 25,50/kg)"
    )
    
    # Valor total em centavos
    valor_total_centavos = models.IntegerField(
        help_text="Valor total da compra em centavos"
    )
    
    data_compra = models.DateField(default=timezone.now)
    numero_nota = models.CharField(max_length=50, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compra de Ingrediente"
        verbose_name_plural = "Compras de Ingredientes"
        ordering = ['-data_compra']

    def __str__(self):
        return f"{self.ingrediente.nome} - {self.quantidade} - {self.data_compra}"

    @property
    def preco_unitario(self):
        """Retorna preço unitário em reais."""
        return self.preco_unitario_centavos / 100

    @property
    def valor_total(self):
        """Retorna valor total em reais."""
        return self.valor_total_centavos / 100

    def save(self, *args, **kwargs):
        """Calcula valor total e atualiza estoque automaticamente."""
        # Calcular valor total
        self.valor_total_centavos = int(self.quantidade * self.preco_unitario_centavos)
        
        super().save(*args, **kwargs)
        
        # Atualizar estoque
        self._atualizar_estoque()
        
        # Criar histórico de preço
        self._criar_historico_preco()

    def _atualizar_estoque(self):
        """Atualiza o estoque do ingrediente."""
        estoque, created = EstoqueIngrediente.objects.get_or_create(
            ingrediente=self.ingrediente,
            defaults={
                'quantidade_atual': 0,
                'unidade_medida': self.unidade,  # Usar a unidade da compra
                'preco_compra_atual_centavos': self.preco_unitario_centavos
            }
        )
        
        # Se estoque foi criado agora, usar a unidade da compra
        if created:
            estoque.unidade_medida = self.unidade
        
        # Converter quantidade para a unidade do estoque
        quantidade_convertida = self._converter_quantidade_para_estoque(estoque)
        
        # Adicionar quantidade ao estoque
        estoque.quantidade_atual += quantidade_convertida
        estoque.data_ultima_compra = self.data_compra
        
        # Atualizar preço (convertendo para a unidade do estoque)
        preco_convertido = self._converter_preco_para_estoque(estoque)
        estoque.preco_compra_atual_centavos = preco_convertido
        estoque.save()

    def _converter_quantidade_para_estoque(self, estoque):
        """Converte quantidade da compra para a unidade do estoque."""
        if self.unidade == estoque.unidade_medida:
            return self.quantidade
        
        # Conversão entre unidades
        try:
            if self.unidade == 'g' and estoque.unidade_medida == 'kg':
                return self.quantidade / 1000
            elif self.unidade == 'kg' and estoque.unidade_medida == 'g':
                return self.quantidade * 1000
            else:
                # Não é possível converter entre unidade e peso
                raise ValueError(f"Não é possível converter {self.unidade} para {estoque.unidade_medida}")
        except ValueError:
            # Se não conseguir converter, manter unidade da compra no estoque
            estoque.unidade_medida = self.unidade
            estoque.save()
            return self.quantidade

    def _converter_preco_para_estoque(self, estoque):
        """Converte preço da compra para a unidade do estoque."""
        if self.unidade == estoque.unidade_medida:
            return self.preco_unitario_centavos
        
        # Conversão de preços
        try:
            if self.unidade == 'g' and estoque.unidade_medida == 'kg':
                return self.preco_unitario_centavos * 1000  # preço/g → preço/kg
            elif self.unidade == 'kg' and estoque.unidade_medida == 'g':
                return self.preco_unitario_centavos // 1000  # preço/kg → preço/g
            else:
                return self.preco_unitario_centavos
        except:
            return self.preco_unitario_centavos

    def _criar_historico_preco(self):
        """Cria registro no histórico de preços."""
        HistoricoPrecoCompra.objects.create(
            ingrediente=self.ingrediente,
            preco_centavos=self.preco_unitario_centavos,
            data_preco=self.data_compra,
            fornecedor=self.fornecedor.nome if self.fornecedor else "Não informado",
            compra=self
        )


class HistoricoPrecoCompra(models.Model):
    """Histórico de preços de compra dos ingredientes."""
    
    ingrediente = models.ForeignKey(
        Ingrediente,
        on_delete=models.CASCADE,
        related_name="historico_precos"
    )
    preco_centavos = models.IntegerField(
        help_text="Preço em centavos"
    )
    data_preco = models.DateField()
    fornecedor = models.CharField(max_length=120)
    compra = models.ForeignKey(
        CompraIngrediente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Preço"
        verbose_name_plural = "Histórico de Preços"
        ordering = ['-data_preco']

    def __str__(self):
        return f"{self.ingrediente.nome} - R$ {self.preco / 100:.2f} - {self.data_preco}"

    @property
    def preco(self):
        """Retorna preço em reais."""
        return self.preco_centavos / 100
