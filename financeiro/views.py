from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
from .forms import DespesaOperacionalForm, TipoDespesaForm


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


@login_required
def relatorio_vendas(request):
    """Relatório detalhado de vendas com filtros e análises."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    categoria_id = request.GET.get('categoria')
    
    if not data_inicio:
        data_inicio = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not data_fim:
        data_fim = timezone.now().date().strftime('%Y-%m-%d')
    
    # Converter para date
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Filtrar pedidos
    pedidos = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__date__gte=data_inicio,
        data_criacao__date__lte=data_fim
    )
    
    if categoria_id:
        pedidos = pedidos.filter(itens__produto__categoria_id=categoria_id)
    
    # Estatísticas
    stats = {
        'receita_total': pedidos.aggregate(total=Sum('total'))['total'] or 0,
        'quantidade_pedidos': pedidos.count(),
        'ticket_medio': 0
    }
    if stats['quantidade_pedidos'] > 0:
        stats['ticket_medio'] = stats['receita_total'] / stats['quantidade_pedidos']
    
    # Vendas por dia
    vendas_por_dia = pedidos.values('data_criacao__date').annotate(
        receita=Sum('total'),
        pedidos=Count('id')
    ).order_by('data_criacao__date')
    
    # Calcular ticket médio por dia
    for venda in vendas_por_dia:
        if venda['pedidos'] > 0:
            venda['ticket_medio_dia'] = venda['receita'] / venda['pedidos']
        else:
            venda['ticket_medio_dia'] = 0
    
    # Produtos mais vendidos
    produtos_vendidos = pedidos.values('itens__produto__nome').annotate(
        quantidade_vendida=Sum('itens__quantidade'),
        receita_produto=Sum('itens__valor_unitario')
    ).order_by('-receita_produto')[:10]
    
    # Vendas por forma de pagamento
    vendas_por_pagamento = pedidos.values('forma_pagamento').annotate(
        receita=Sum('total')
    ).order_by('-receita')
    
    # Categorias para filtro
    from produtos.models import CategoriaProduto
    categorias = CategoriaProduto.objects.filter(pizzaria=pizzaria)
    
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'categoria_selecionada': categoria_id,
        'stats': stats,
        'vendas_por_dia': vendas_por_dia,
        'produtos_vendidos': produtos_vendidos,
        'vendas_por_pagamento': vendas_por_pagamento,
        'categorias': categorias,
    }
    return render(request, 'financeiro/relatorio_vendas.html', context)


@login_required
def relatorio_custos(request):
    """Relatório de custos e despesas com análises."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if not data_inicio:
        data_inicio = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not data_fim:
        data_fim = timezone.now().date().strftime('%Y-%m-%d')
    
    # Converter para date
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Custos de estoque
    compras = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        data_compra__gte=data_inicio,
        data_compra__lte=data_fim
    )
    custo_estoque = compras.aggregate(total=Sum('valor_total_centavos'))['total'] or 0
    custo_estoque = custo_estoque / 100
    
    # Despesas operacionais
    despesas = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        data_vencimento__gte=data_inicio,
        data_vencimento__lte=data_fim
    )
    despesas_pagas = despesas.filter(pago=True).aggregate(total=Sum('valor_centavos'))['total'] or 0
    despesas_pagas = despesas_pagas / 100
    despesas_pendentes = despesas.filter(pago=False).aggregate(total=Sum('valor_centavos'))['total'] or 0
    despesas_pendentes = despesas_pendentes / 100
    
    custo_total = custo_estoque + despesas_pagas
    
    # Compras por ingrediente
    compras_por_ingrediente = compras.values('ingrediente__nome').annotate(
        valor_total=Sum('valor_total_centavos')
    ).order_by('-valor_total')[:10]
    
    # Despesas por tipo
    despesas_por_tipo = despesas.filter(pago=True).values('tipo_despesa__nome').annotate(
        valor_total=Sum('valor_centavos')
    ).order_by('-valor_total')
    
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'custo_estoque': custo_estoque,
        'despesas_pagas': despesas_pagas,
        'despesas_pendentes': despesas_pendentes,
        'custo_total': custo_total,
        'compras_por_ingrediente': compras_por_ingrediente,
        'despesas_por_tipo': despesas_por_tipo,
    }
    return render(request, 'financeiro/relatorio_custos.html', context)


@login_required
def fluxo_caixa(request):
    """Controle de fluxo de caixa com entradas e saídas."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if not data_inicio:
        data_inicio = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not data_fim:
        data_fim = timezone.now().date().strftime('%Y-%m-%d')
    
    # Converter para date
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    # Movimentações do período
    movimentacoes = MovimentacaoCaixa.objects.filter(
        pizzaria=pizzaria,
        data_movimentacao__date__gte=data_inicio,
        data_movimentacao__date__lte=data_fim
    ).order_by('data_movimentacao')
    
    # Calcular totais
    entradas = movimentacoes.filter(tipo='ENTRADA').aggregate(total=Sum('valor_centavos'))['total'] or 0
    entradas = entradas / 100
    saidas = movimentacoes.filter(tipo='SAIDA').aggregate(total=Sum('valor_centavos'))['total'] or 0
    saidas = saidas / 100
    saldo = entradas - saidas
    
    # Entradas por forma de pagamento
    entradas_por_pagamento = movimentacoes.filter(tipo='ENTRADA').values('forma_pagamento').annotate(
        receita=Sum('valor_centavos')
    ).order_by('-receita')
    
    # Saídas por origem
    saidas_por_origem = movimentacoes.filter(tipo='SAIDA').values('origem').annotate(
        valor_total=Sum('valor_centavos')
    ).order_by('-valor_total')
    
    context = {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'entradas': entradas,
        'saidas': saidas,
        'saldo': saldo,
        'movimentacoes': movimentacoes,
        'entradas_por_pagamento': entradas_por_pagamento,
        'saidas_por_origem': saidas_por_origem,
    }
    return render(request, 'financeiro/fluxo_caixa.html', context)


@login_required
def metas_vendas(request):
    """Gestão e acompanhamento de metas de vendas."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    ano = request.GET.get('ano', timezone.now().year)
    mes = request.GET.get('mes', '')
    
    # Filtrar metas
    metas_queryset = MetaVenda.objects.filter(pizzaria=pizzaria, ano=ano)
    if mes:
        metas_queryset = metas_queryset.filter(mes=mes)
    
    # Preparar dados das metas
    metas = []
    for meta in metas_queryset:
        # Calcular realização (simplificado)
        realizacao = {
            'receita_realizada': 0,
            'quantidade_realizada': 0,
            'ticket_medio_realizado': 0,
            'percentual_receita': 0,
            'percentual_quantidade': 0,
            'percentual_ticket': 0,
        }
        
        # Aqui você implementaria a lógica real de cálculo
        # Por enquanto, valores fictícios para demonstração
        if meta.tipo_meta == 'RECEITA':
            realizacao['receita_realizada'] = meta.meta_receita_centavos * 0.75 / 100  # 75% da meta
            realizacao['percentual_receita'] = 75
        elif meta.tipo_meta == 'QUANTIDADE':
            realizacao['quantidade_realizada'] = int(meta.meta_quantidade * 0.8)  # 80% da meta
            realizacao['percentual_quantidade'] = 80
        elif meta.tipo_meta == 'TICKET_MEDIO':
            realizacao['ticket_medio_realizado'] = meta.meta_ticket_medio_centavos * 0.9 / 100  # 90% da meta
            realizacao['percentual_ticket'] = 90
        
        metas.append({
            'meta': meta,
            'realizacao': realizacao
        })
    
    # Anos disponíveis
    anos_disponiveis = MetaVenda.objects.filter(pizzaria=pizzaria).values_list('ano', flat=True).distinct().order_by('-ano')
    
    # Meses para filtro
    meses = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    context = {
        'metas': metas,
        'ano_selecionado': int(ano),
        'mes_selecionado': int(mes) if mes else None,
        'anos_disponiveis': anos_disponiveis,
        'meses': meses,
    }
    return render(request, 'financeiro/metas_vendas.html', context)


@login_required
def despesas_operacionais(request):
    """Gestão de despesas operacionais com filtros e controles."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    status = request.GET.get('status', 'todas')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Filtrar despesas
    despesas = DespesaOperacional.objects.filter(pizzaria=pizzaria)
    
    if status == 'pendentes':
        despesas = despesas.filter(pago=False)
    elif status == 'pagas':
        despesas = despesas.filter(pago=True)
    elif status == 'atrasadas':
        despesas = despesas.filter(pago=False, data_vencimento__lt=timezone.now().date())
    
    if data_inicio:
        despesas = despesas.filter(data_vencimento__gte=data_inicio)
    if data_fim:
        despesas = despesas.filter(data_vencimento__lte=data_fim)
    
    # Calcular totais
    total_pendente = despesas.filter(pago=False).aggregate(total=Sum('valor_centavos'))['total'] or 0
    total_pendente = total_pendente / 100
    total_pago = despesas.filter(pago=True).aggregate(total=Sum('valor_centavos'))['total'] or 0
    total_pago = total_pago / 100
    
    context = {
        'despesas': despesas,
        'filtro_status': status,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_pendente': total_pendente,
        'total_pago': total_pago,
    }
    return render(request, 'financeiro/despesas_operacionais.html', context)


@login_required
def adicionar_despesa(request):
    """Adicionar nova despesa operacional."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    if request.method == 'POST':
        form = DespesaOperacionalForm(request.POST)
        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.pizzaria = pizzaria
            despesa.save()
            
            messages.success(request, 'Despesa operacional registrada com sucesso!')
            return redirect('financeiro:despesas_operacionais')
    else:
        form = DespesaOperacionalForm()
    
    context = {
        'form': form,
        'titulo': 'Nova Despesa Operacional',
        'acao': 'Adicionar'
    }
    return render(request, 'financeiro/form_despesa.html', context)


@login_required
def editar_despesa(request, despesa_id):
    """Editar despesa operacional existente."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    despesa = get_object_or_404(DespesaOperacional, id=despesa_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        form = DespesaOperacionalForm(request.POST, instance=despesa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despesa operacional atualizada com sucesso!')
            return redirect('financeiro:despesas_operacionais')
    else:
        form = DespesaOperacionalForm(instance=despesa)
    
    context = {
        'form': form,
        'despesa': despesa,
        'titulo': 'Editar Despesa Operacional',
        'acao': 'Atualizar'
    }
    return render(request, 'financeiro/form_despesa.html', context)


@login_required
def excluir_despesa(request, despesa_id):
    """Excluir despesa operacional."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    despesa = get_object_or_404(DespesaOperacional, id=despesa_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        descricao = despesa.descricao
        despesa.delete()
        messages.success(request, f'Despesa "{descricao}" excluída com sucesso!')
        return redirect('financeiro:despesas_operacionais')
    
    context = {
        'despesa': despesa
    }
    return render(request, 'financeiro/confirmar_exclusao_despesa.html', context)


@login_required
def marcar_despesa_paga(request, despesa_id):
    """Marca despesa como paga."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    despesa = get_object_or_404(DespesaOperacional, id=despesa_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        despesa.marcar_como_paga()
        messages.success(request, f'Despesa "{despesa.descricao}" marcada como paga!')
        return redirect('financeiro:despesas_operacionais')
    
    context = {
        'despesa': despesa
    }
    return render(request, 'financeiro/confirmar_pagamento_despesa.html', context)


@login_required
def adicionar_tipo_despesa(request):
    """Adicionar novo tipo de despesa."""
    if request.method == 'POST':
        form = TipoDespesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de despesa criado com sucesso!')
            return redirect('financeiro:despesas_operacionais')
    else:
        form = TipoDespesaForm()
    
    context = {
        'form': form,
        'titulo': 'Novo Tipo de Despesa',
        'acao': 'Adicionar'
    }
    return render(request, 'financeiro/form_tipo_despesa.html', context)
