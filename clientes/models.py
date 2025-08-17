from django.db import models
from django.utils import timezone
from autenticacao.models import Pizzaria


class Cliente(models.Model):
    """Cliente de uma pizzaria específica."""
    
    pizzaria = models.ForeignKey(
        Pizzaria,
        on_delete=models.CASCADE,
        related_name="clientes"
    )
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    
    # Endereço principal (referência para o endereço padrão)
    endereco_principal = models.ForeignKey(
        'EnderecoCliente', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cliente_principal'
    )
    
    # Informações adicionais
    data_nascimento = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    
    # Controle
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(default=timezone.now)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        unique_together = ('pizzaria', 'telefone')  # Telefone único por pizzaria
        ordering = ('nome',)
    
    def __str__(self):
        return f"{self.nome} - {self.telefone}"
    
    def total_gasto(self):
        """Retorna o total gasto pelo cliente"""
        return self.pedidos.aggregate(
            total=models.Sum('total')
        )['total'] or 0
    
    def total_pedidos(self):
        """Retorna o número total de pedidos"""
        return self.pedidos.count()
    
    def ultimo_pedido(self):
        """Retorna o último pedido do cliente"""
        return self.pedidos.order_by('-data_criacao').first()
    
    def pedidos_por_status(self):
        """Retorna estatísticas de pedidos por status"""
        return self.pedidos.values('status').annotate(
            count=models.Count('id')
        )
    
    def ticket_medio(self):
        """Retorna o ticket médio do cliente"""
        total_pedidos = self.total_pedidos()
        if total_pedidos == 0:
            return 0
        return self.total_gasto() / total_pedidos
    
    def produtos_favoritos(self, limit=3):
        """Retorna os produtos mais pedidos pelo cliente"""
        from pedidos.models import ItemPedido
        return ItemPedido.objects.filter(
            pedido__cliente=self,
            pedido__status__in=['ENTREGUE']
        ).values(
            'produto__nome'
        ).annotate(
            quantidade_total=models.Sum('quantidade')
        ).order_by('-quantidade_total')[:limit]


class EnderecoCliente(models.Model):
    """Endereços de entrega de um cliente."""
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="enderecos"
    )
    nome = models.CharField(max_length=50, help_text="Ex: Casa, Trabalho")
    cep = models.CharField(max_length=10)
    rua = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    referencia = models.CharField(max_length=200, blank=True, help_text="Ponto de referência")
    
    class Meta:
        verbose_name = "Endereço do Cliente"
        verbose_name_plural = "Endereços dos Clientes"
        ordering = ('nome',)
    
    def __str__(self):
        return f"{self.nome} - {self.cliente.nome}"
    
    def endereco_completo(self):
        """Retorna o endereço formatado"""
        endereco = f"{self.rua}, {self.numero}"
        if self.complemento:
            endereco += f", {self.complemento}"
        endereco += f" - {self.bairro}, {self.cidade}/{self.estado}"
        endereco += f" - CEP: {self.cep}"
        return endereco