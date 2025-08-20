from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

from autenticacao.decorators import super_admin_required
from autenticacao.models import Pizzaria
from pedidos.models import Pedido
from estoque.models import CompraIngrediente
from produtos.models import Produto
from .models import DespesaOperacional, MovimentacaoCaixa, MetaVenda, TipoDespesa


def dashboard_financeiro(request):
    """Dashboard principal do financeiro."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    # Dados do mês atual
    pedidos_mes = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__date__gte=inicio_mes,
        data_criacao__date__lte=hoje
    )
    
    # Receitas
    receita_hoje = pedidos_mes.filter(data_criacao__date=hoje).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    receita_mes = pedidos_mes.aggregate(total=Sum('total'))['total'] or 0
    
    # Custos do mês
    compras_mes = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        data_compra__gte=inicio_mes,
        data_compra__lte=hoje
    ).aggregate(total=Sum('valor_total_centavos'))['total'] or 0
    
    despesas_mes = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        data_vencimento__gte=inicio_mes,
        data_vencimento__lte=hoje,
        pago=True
    ).aggregate(total=Sum('valor_centavos'))['total'] or 0
    
    # Calcular lucro
    custo_total_mes_centavos = compras_mes + despesas_mes
    custo_total_mes = custo_total_mes_centavos / 100
    lucro_mes = float(receita_mes) - custo_total_mes
    
    # Margem
    margem_mes = (lucro_mes / float(receita_mes) * 100) if receita_mes > 0 else 0
    
    # Pedidos
    pedidos_hoje = pedidos_mes.filter(data_criacao__date=hoje).count()
    pedidos_mes_count = pedidos_mes.count()
    
    # Ticket médio
    ticket_medio_mes = float(receita_mes) / pedidos_mes_count if pedidos_mes_count > 0 else 0
    
    # Despesas em atraso
    despesas_atraso = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        pago=False,
        data_vencimento__lt=hoje
    ).count()
    
    # Movimentações recentes
    movimentacoes_recentes = MovimentacaoCaixa.objects.filter(
        pizzaria=pizzaria
    ).select_related('pedido', 'despesa', 'compra_estoque').order_by('-data_movimentacao')[:10]
    
    context = {
        # Receitas
        'receita_hoje': receita_hoje,
        'receita_mes': receita_mes,
        
        # Custos e Lucro
        'custo_mes': custo_total_mes,
        'lucro_mes': lucro_mes,
        'margem_mes': margem_mes,
        
        # Pedidos
        'pedidos_hoje': pedidos_hoje,
        'pedidos_mes': pedidos_mes_count,
        'ticket_medio_mes': ticket_medio_mes,
        
        # Alertas
        'despesas_atraso': despesas_atraso,
        
        # Listas
        'movimentacoes_recentes': movimentacoes_recentes,
        
        # Período
        'mes_atual': hoje.strftime('%B/%Y'),
    }
    
    return render(request, 'financeiro/dashboard.html', context)
