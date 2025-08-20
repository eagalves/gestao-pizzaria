from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
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
    """Despesas operacionais da pizzaria (incluindo fixas mensais)."""
    
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
    
    # Campos para despesas recorrentes/fixas mensais
    recorrente = models.BooleanField(
        default=False, 
        help_text="Se esta despesa se repete mensalmente"
    )
    dia_vencimento_recorrente = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Dia do mês para vencimento (1-31) - apenas para despesas recorrentes"
    )
    data_inicio_recorrencia = models.DateField(
        null=True, 
        blank=True,
        help_text="Data de início da recorrência mensal"
    )
    data_fim_recorrencia = models.DateField(
        null=True, 
        blank=True,
        help_text="Data de fim da recorrência (deixe em branco para indefinido)"
    )
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Despesa Operacional"
        verbose_name_plural = "Despesas Operacionais"
        ordering = ['-data_vencimento']
    
    def __str__(self):
        if self.recorrente:
            return f"{self.descricao} - R$ {self.valor:.2f} (Recorrente - Dia {self.dia_vencimento_recorrente})"
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
    
    @property
    def despesa_fixa_mensal(self):
        """Verifica se é uma despesa fixa mensal (recorrente)."""
        return self.recorrente and self.tipo == 'FIXA'
    
    def marcar_como_paga(self, data_pagamento=None):
        """Marca despesa como paga."""
        self.pago = True
        self.data_pagamento = data_pagamento or timezone.now().date()
        self.save()
    
    def gerar_despesa_mensal(self, mes, ano):
        """Gera uma despesa mensal para o mês/ano especificado (apenas para despesas recorrentes)."""
        if not self.recorrente:
            return None
            
        from datetime import date, timedelta
        
        # Calcular data de vencimento
        try:
            data_vencimento = date(ano, mes, self.dia_vencimento_recorrente)
        except ValueError:
            # Se o dia não existe no mês (ex: 31 em fevereiro), usar o último dia do mês
            if mes == 12:
                data_vencimento = date(ano + 1, 1, 1) - timedelta(days=1)
            else:
                data_vencimento = date(ano, mes + 1, 1) - timedelta(days=1)
        
        # Verificar se já existe despesa para este mês/ano
        if DespesaOperacional.objects.filter(
            pizzaria=self.pizzaria,
            descricao__icontains=self.descricao,
            data_vencimento__year=ano,
            data_vencimento__month=mes,
            recorrente=False  # Apenas despesas mensais geradas
        ).exists():
            return None  # Já existe despesa para este mês
        
        # Criar nova despesa mensal
        despesa_mensal = DespesaOperacional.objects.create(
            pizzaria=self.pizzaria,
            tipo_despesa=self.tipo_despesa,
            descricao=f"{self.descricao} ({mes:02d}/{ano})",
            valor_centavos=self.valor_centavos,
            tipo='FIXA',
            forma_pagamento=self.forma_pagamento,
            data_vencimento=data_vencimento,
            observacoes=f"Gerada automaticamente da despesa fixa mensal: {self.descricao}",
            recorrente=False,  # Esta é a despesa mensal, não a recorrente
            dia_vencimento_recorrente=None,
            data_inicio_recorrencia=None,
            data_fim_recorrencia=None
        )
        
        return despesa_mensal
    
    def gerar_despesas_pendentes(self):
        """Gera despesas mensais para meses pendentes (apenas para despesas recorrentes)."""
        if not self.recorrente:
            return []
            
        from datetime import date, timedelta
        
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # Gerar despesas para o mês atual e próximos 2 meses
        despesas_criadas = []
        for i in range(3):
            mes = mes_atual + i
            ano = ano_atual
            
            # Ajustar mês e ano se passar de 12
            if mes > 12:
                mes -= 12
                ano += 1
            
            # Verificar se está dentro do período de vigência
            if self.data_fim_recorrencia and date(ano, mes, 1) > self.data_fim_recorrencia:
                continue
            
            if date(ano, mes, 1) >= self.data_inicio_recorrencia:
                despesa = self.gerar_despesa_mensal(mes, ano)
                if despesa:
                    despesas_criadas.append(despesa)
        
        return despesas_criadas


class MovimentacaoCaixa(models.Model):
    """Movimentações de caixa da pizzaria."""
    
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]
    
    ORIGEM_CHOICES = [
        ('VENDA', 'Venda'),
        ('COMPRA', 'Compra de Estoque'),
        ('DESPESA', 'Despesa Operacional'),
        ('OUTROS', 'Outros'),
    ]
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="movimentacoes"
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES)
    descricao = models.CharField(max_length=200)
    
    # Valor em centavos
    valor_centavos = models.IntegerField()
    
    forma_pagamento = models.CharField(max_length=3, choices=DespesaOperacional.FORMA_PAGAMENTO_CHOICES)
    data_movimentacao = models.DateTimeField()
    
    # Relacionamentos opcionais
    pedido = models.ForeignKey(
        'pedidos.Pedido',
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
    despesa = models.ForeignKey(
        DespesaOperacional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes"
    )
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Movimentação de Caixa"
        verbose_name_plural = "Movimentações de Caixa"
        ordering = ['-data_movimentacao']
    
    def __str__(self):
        sinal = '+' if self.tipo == 'ENTRADA' else '-'
        return f"{sinal}R$ {self.valor:.2f} - {self.descricao}"
    
    @property
    def valor(self):
        """Retorna valor em reais."""
        return self.valor_centavos / 100


class MetaVenda(models.Model):
    """Metas de vendas mensais da pizzaria."""
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="metas_venda"
    )
    ano = models.IntegerField()
    mes = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    
    # Meta de receita em centavos
    meta_receita_centavos = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Meta de receita em centavos"
    )
    
    # Meta de ticket médio em centavos
    meta_ticket_medio_centavos = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Meta de ticket médio em centavos"
    )
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Meta de Venda"
        verbose_name_plural = "Metas de Venda"
        unique_together = ['pizzaria', 'ano', 'mes']
        ordering = ['-ano', '-mes']
    
    def __str__(self):
        return f"Meta {self.mes:02d}/{self.ano} - R$ {self.meta_receita:.2f}"
    
    @property
    def meta_receita(self):
        """Retorna meta de receita em reais."""
        return self.meta_receita_centavos / 100
    
    @property
    def meta_ticket_medio(self):
        """Retorna meta de ticket médio em reais."""
        return self.meta_ticket_medio_centavos / 100
