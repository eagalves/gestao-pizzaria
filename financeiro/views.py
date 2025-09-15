from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta, date
import calendar

from autenticacao.decorators import super_admin_required
from autenticacao.models import Pizzaria
from pedidos.models import Pedido
from estoque.models import CompraIngrediente
from produtos.models import Produto
from .models import DespesaOperacional, MovimentacaoCaixa, MetaVenda, TipoDespesa
from .forms import DespesaOperacionalForm, TipoDespesaForm


@login_required
def dashboard_financeiro(request):
    """Dashboard financeiro da pizzaria."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Período para análise (últimos 30 dias)
    hoje = timezone.now().date()
    data_inicio = hoje - timedelta(days=30)
    
    # Receitas (pedidos entregues)
    receitas = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__gte=data_inicio
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Converter para float se for Decimal
    if hasattr(receitas, 'quantize'):
        receitas = float(receitas)
    
    # Despesas operacionais
    despesas = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        data_vencimento__gte=data_inicio
    ).aggregate(total=Sum('valor_centavos'))['total'] or 0
    despesas = float(despesas) / 100
    
    # Despesas recorrentes (fixas mensais)
    despesas_recorrentes = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        recorrente=True
    ).aggregate(total=Sum('valor_centavos'))['total'] or 0
    despesas_recorrentes = float(despesas_recorrentes) / 100
    
    # Lucro
    lucro = receitas - despesas
    
    # Margem de lucro
    margem = (lucro / receitas * 100) if receitas > 0 else 0
    
    # Despesas por tipo
    despesas_por_tipo = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        data_vencimento__gte=data_inicio
    ).values('tipo_despesa__nome').annotate(
        total=Sum('valor_centavos')
    ).order_by('-total')
    
    # Despesas recorrentes ativas
    despesas_recorrentes_ativas = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        recorrente=True
    ).count()
    
    # Calcular métricas para hoje
    hoje = timezone.now().date()
    receita_hoje = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__date=hoje
    ).aggregate(total=Sum('total'))['total'] or 0
    
    if hasattr(receita_hoje, 'quantize'):
        receita_hoje = float(receita_hoje)
    
    pedidos_hoje = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__date=hoje
    ).count()
    
    # Calcular métricas do mês
    mes_atual = hoje.replace(day=1)
    receita_mes = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__gte=mes_atual
    ).aggregate(total=Sum('total'))['total'] or 0
    
    if hasattr(receita_mes, 'quantize'):
        receita_mes = float(receita_mes)
    
    pedidos_mes = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__gte=mes_atual
    ).count()
    
    # Custos do mês (compras de ingredientes)
    custo_mes = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        data_compra__gte=mes_atual
    ).aggregate(total=Sum('valor_total_centavos'))['total'] or 0
    custo_mes = float(custo_mes) / 100
    
    # Lucro e margem do mês
    lucro_mes = receita_mes - custo_mes
    margem_mes = (lucro_mes / receita_mes * 100) if receita_mes > 0 else 0
    
    # Ticket médio do mês
    ticket_medio_mes = (receita_mes / pedidos_mes) if pedidos_mes > 0 else 0
    
    # Despesas em atraso
    despesas_atraso = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        data_vencimento__lt=hoje,
        pago=False
    ).count()
    
    # Movimentações recentes (últimos 10 dias)
    data_inicio_recente = hoje - timedelta(days=10)
    movimentacoes_recentes = []
    
    # Adicionar pedidos entregues como entradas
    pedidos_recentes = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__gte=data_inicio_recente
    ).order_by('-data_criacao')[:5]
    
    for pedido in pedidos_recentes:
        movimentacoes_recentes.append({
            'data_movimentacao': pedido.data_criacao,
            'descricao': f'Venda - Pedido #{pedido.id}',
            'tipo': 'ENTRADA',
            'valor': pedido.total,
            'forma_pagamento': 'Dinheiro'  # Default
        })
    
    # Adicionar compras recentes como saídas
    compras_recentes = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        data_compra__gte=data_inicio_recente
    ).order_by('-data_compra')[:5]
    
    for compra in compras_recentes:
        movimentacoes_recentes.append({
            'data_movimentacao': compra.data_compra,
            'descricao': f'Compra - {compra.ingrediente.nome}',
            'tipo': 'SAIDA',
            'valor': compra.valor_total_centavos / 100,
            'forma_pagamento': 'Dinheiro'  # Default
        })
    
    # Ordenar por data (mais recente primeiro)
    # Converter todas as datas para datetime para evitar problemas de comparação
    for mov in movimentacoes_recentes:
        if isinstance(mov['data_movimentacao'], date):
            mov['data_movimentacao'] = datetime.combine(mov['data_movimentacao'], datetime.min.time())
    
    movimentacoes_recentes.sort(key=lambda x: x['data_movimentacao'], reverse=True)
    movimentacoes_recentes = movimentacoes_recentes[:10]  # Limitar a 10
    
    context = {
        'mes_atual': hoje.strftime('%B/%Y'),
        'receita_hoje': receita_hoje,
        'receita_mes': receita_mes,
        'custo_mes': custo_mes,
        'lucro_mes': lucro_mes,
        'margem_mes': margem_mes,
        'pedidos_hoje': pedidos_hoje,
        'pedidos_mes': pedidos_mes,
        'ticket_medio_mes': ticket_medio_mes,
        'despesas_atraso': despesas_atraso,
        'movimentacoes_recentes': movimentacoes_recentes,
        'receitas': receitas,
        'despesas': despesas,
        'despesas_recorrentes': despesas_recorrentes,
        'lucro': lucro,
        'margem': margem,
        'despesas_por_tipo': despesas_por_tipo,
        'despesas_recorrentes_ativas': despesas_recorrentes_ativas,
        'periodo_dias': 30
    }
    return render(request, 'financeiro/dashboard.html', context)


@login_required
def relatorio_vendas(request):
    """Relatório de vendas da pizzaria."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    categoria_id = request.GET.get('categoria')
    
    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = timezone.now().date() - timedelta(days=30)
            data_fim = timezone.now().date()
    else:
        # Período padrão (últimos 30 dias)
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
    
    # Converter datas (date) para datetimes conscientes de fuso para comparar com DateTimeField
    inicio_dt = timezone.make_aware(datetime.combine(data_inicio, datetime.min.time()))
    fim_dt = timezone.make_aware(datetime.combine(data_fim, datetime.max.time()))
    
    # Pedidos entregues no período
    pedidos = Pedido.objects.filter(
        pizzaria=pizzaria,
        status='ENTREGUE',
        data_criacao__gte=inicio_dt,
        data_criacao__lte=fim_dt
    ).order_by('-data_criacao')
    print(pedidos)
    # Filtrar por categoria se especificado
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            pedidos = pedidos.filter(itens__produto__categoria_id=categoria_id).distinct()
        except ValueError:
            pass
    
    # Total de vendas
    total_vendas = pedidos.aggregate(total=Sum('total'))['total'] or 0
    
    # Converter para float se for Decimal
    if hasattr(total_vendas, 'quantize'):
        total_vendas = float(total_vendas)
    
    # Quantidade de pedidos
    quantidade_pedidos = pedidos.count()
    
    # Ticket médio
    ticket_medio = total_vendas / quantidade_pedidos if quantidade_pedidos > 0 else 0
    
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
        # Adicionar campo data_criacao para o template
        venda['data_criacao'] = venda['data_criacao__date']
        # Converter para float se for Decimal
        if hasattr(venda['receita'], 'quantize'):
            venda['receita'] = float(venda['receita'])
        if hasattr(venda['ticket_medio_dia'], 'quantize'):
            venda['ticket_medio_dia'] = float(venda['ticket_medio_dia'])
        # Converter para int se for Decimal
        if hasattr(venda['pedidos'], 'quantize'):
            venda['pedidos'] = int(venda['pedidos'])
    
    # Vendas por forma de pagamento
    vendas_por_pagamento = pedidos.values('forma_pagamento').annotate(
        receita=Sum('total'),  # Nome que o template espera
        quantidade=Count('id')
    ).order_by('-receita')
    
    # Adicionar nome da forma de pagamento para o template
    for venda in vendas_por_pagamento:
        venda['forma_pagamento_nome'] = dict(Pedido.FORMA_PAGAMENTO_CHOICES).get(venda['forma_pagamento'], venda['forma_pagamento'])
        # Converter para float se for Decimal
        if hasattr(venda['receita'], 'quantize'):
            venda['receita'] = float(venda['receita'])
        # Converter para int se for Decimal
        if hasattr(venda['quantidade'], 'quantize'):
            venda['quantidade'] = int(venda['quantidade'])
    
    # Top 10 produtos mais vendidos
    produtos_vendidos = pedidos.values('itens__produto__nome').annotate(
        quantidade_vendida=Sum('itens__quantidade'),
        receita_produto=Sum(F('itens__quantidade') * F('itens__valor_unitario'))
    ).order_by('-quantidade_vendida')[:10]
    
    # Adicionar nome do produto para o template
    for produto in produtos_vendidos:
        produto['produto_nome'] = produto['itens__produto__nome']
        # Converter para float se for Decimal
        if hasattr(produto['receita_produto'], 'quantize'):
            produto['receita_produto'] = float(produto['receita_produto'])
        # Converter para int se for Decimal
        if hasattr(produto['quantidade_vendida'], 'quantize'):
            produto['quantidade_vendida'] = int(produto['quantidade_vendida'])
    
    # Categorias disponíveis para filtro
    from produtos.models import CategoriaProduto
    categorias = CategoriaProduto.objects.filter(pizzaria=pizzaria).order_by('nome')
    
    # Objeto stats para o template
    stats = {
        'receita_total': total_vendas,
        'quantidade_pedidos': quantidade_pedidos,
        'ticket_medio': ticket_medio
    }
    
    context = {
        'pedidos': pedidos,
        'total_vendas': total_vendas,
        'quantidade_pedidos': quantidade_pedidos,
        'ticket_medio': ticket_medio,
        'vendas_por_dia': vendas_por_dia,
        'vendas_por_pagamento': vendas_por_pagamento,
        'produtos_vendidos': produtos_vendidos,
        'categorias': categorias,
        'categoria_selecionada': str(categoria_id) if categoria_id else '',
        'stats': stats,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    return render(request, 'financeiro/relatorio_vendas.html', context)


@login_required
def relatorio_custos(request):
    """Relatório de custos da pizzaria."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = timezone.now().date() - timedelta(days=30)
            data_fim = timezone.now().date()
    else:
        # Período padrão (últimos 30 dias)
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
    
    # Despesas operacionais
    despesas = DespesaOperacional.objects.filter(
        pizzaria=pizzaria,
        data_vencimento__gte=data_inicio,
        data_vencimento__lte=data_fim
    ).order_by('-data_vencimento')
    
    # Total de despesas
    total_despesas = despesas.aggregate(total=Sum('valor_centavos'))['total'] or 0
    total_despesas = float(total_despesas) / 100
    
    # Despesas por tipo
    despesas_por_tipo = despesas.values('tipo_despesa__nome').annotate(
        total=Sum('valor_centavos')
    ).order_by('-total')
    
    # Despesas recorrentes vs variáveis
    despesas_recorrentes = despesas.filter(recorrente=True).aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    despesas_recorrentes = float(despesas_recorrentes) / 100
    
    despesas_variaveis = despesas.filter(recorrente=False).aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    despesas_variaveis = float(despesas_variaveis) / 100
    
    # Despesas em atraso
    despesas_atraso = despesas.filter(
        pago=False,
        data_vencimento__lt=timezone.now().date()
    ).aggregate(total=Sum('valor_centavos'))['total'] or 0
    despesas_atraso = float(despesas_atraso) / 100
    
    # Custo de estoque (compras de ingredientes)
    custo_estoque = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        data_compra__gte=data_inicio,
        data_compra__lte=data_fim
    ).aggregate(total=Sum('valor_total_centavos'))['total'] or 0
    custo_estoque = float(custo_estoque) / 100
    
    # Despesas pagas
    despesas_pagas = despesas.filter(pago=True).aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    despesas_pagas = float(despesas_pagas) / 100
    
    # Despesas pendentes
    despesas_pendentes = despesas.filter(pago=False).aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    despesas_pendentes = float(despesas_pendentes) / 100
    
    # Custo total
    custo_total = custo_estoque + despesas_pagas + despesas_pendentes
    
    context = {
        'despesas': despesas,
        'total_despesas': total_despesas,
        'despesas_por_tipo': despesas_por_tipo,
        'despesas_recorrentes': despesas_recorrentes,
        'despesas_variaveis': despesas_variaveis,
        'despesas_atraso': despesas_atraso,
        'custo_estoque': custo_estoque,
        'despesas_pagas': despesas_pagas,
        'despesas_pendentes': despesas_pendentes,
        'custo_total': custo_total,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    return render(request, 'financeiro/relatorio_custos.html', context)


@login_required
def fluxo_caixa(request):
    """Fluxo de caixa da pizzaria."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    if data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = timezone.now().date() - timedelta(days=30)
            data_fim = timezone.now().date()
    else:
        # Período padrão (últimos 30 dias)
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
    
    # Movimentações de caixa
    movimentacoes = MovimentacaoCaixa.objects.filter(
        pizzaria=pizzaria,
        data_movimentacao__date__gte=data_inicio,
        data_movimentacao__date__lte=data_fim
    ).order_by('-data_movimentacao')
    
    # Total de entradas e saídas
    total_entradas = movimentacoes.filter(tipo='ENTRADA').aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    total_entradas = float(total_entradas) / 100
    
    total_saidas = movimentacoes.filter(tipo='SAIDA').aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    total_saidas = float(total_saidas) / 100
    
    saldo = total_entradas - total_saidas
    
    # Movimentações por origem
    saidas_por_origem = movimentacoes.filter(tipo='SAIDA').values('origem').annotate(
        total=Sum('valor_centavos')
    ).order_by('-total')
    
    # Entradas por forma de pagamento
    entradas_por_pagamento = movimentacoes.filter(tipo='ENTRADA').values('forma_pagamento').annotate(
        total=Sum('valor_centavos')
    ).order_by('-total')
    
    context = {
        'movimentacoes': movimentacoes,
        'entradas': total_entradas,  # Nome que o template espera
        'saidas': total_saidas,      # Nome que o template espera
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo': saldo,
        'saidas_por_origem': saidas_por_origem,  # Nome que o JavaScript espera
        'entradas_por_pagamento': entradas_por_pagamento,
        'data_inicio': data_inicio,
        'data_fim': data_fim
    }
    return render(request, 'financeiro/fluxo_caixa.html', context)


@login_required
def metas_vendas(request):
    """Gestão de metas de vendas."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Ano atual
    ano_atual = timezone.now().year
    
    # Filtros
    ano_selecionado = request.GET.get('ano', ano_atual)
    mes_selecionado = request.GET.get('mes', '')
    
    try:
        ano_selecionado = int(ano_selecionado)
    except ValueError:
        ano_selecionado = ano_atual
    
    # Lista de anos disponíveis (últimos 5 anos)
    anos_disponiveis = list(range(ano_atual - 4, ano_atual + 1))
    
    # Lista de meses
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    
    # Buscar metas do ano selecionado
    metas = MetaVenda.objects.filter(
        pizzaria=pizzaria,
        ano=ano_selecionado
    ).order_by('mes')
    
    # Criar metas para meses que não têm
    meses_existentes = [meta.mes for meta in metas]
    for mes in range(1, 13):
        if mes not in meses_existentes:
            MetaVenda.objects.create(
                pizzaria=pizzaria,
                ano=ano_selecionado,
                mes=mes,
                meta_receita_centavos=0,
                meta_ticket_medio_centavos=0
            )
    
    # Recarregar metas
    metas = MetaVenda.objects.filter(
        pizzaria=pizzaria,
        ano=ano_selecionado
    ).order_by('mes')
    
    # Filtrar por mês se especificado
    if mes_selecionado:
        try:
            mes_selecionado = int(mes_selecionado)
            metas = metas.filter(mes=mes_selecionado)
        except ValueError:
            pass
    
    # Calcular realização para cada meta
    for meta in metas:
        # Receita realizada no mês
        receita_realizada = Pedido.objects.filter(
            pizzaria=pizzaria,
            status='ENTREGUE',
            data_criacao__year=meta.ano,
            data_criacao__month=meta.mes
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Converter para float se for Decimal
        if hasattr(receita_realizada, 'quantize'):
            receita_realizada = float(receita_realizada)
        
        meta.receita_realizada = receita_realizada
        meta.percentual_realizacao = (receita_realizada / meta.meta_receita * 100) if meta.meta_receita > 0 else 0
        
        # Status da meta
        if meta.percentual_realizacao >= 100:
            meta.status = 'ATINGIDA'
        elif meta.percentual_realizacao >= 80:
            meta.status = 'EM_ANDAMENTO'
        else:
            meta.status = 'ATRASADA'
    
    context = {
        'metas': metas,
        'ano_atual': ano_atual,
        'ano_selecionado': ano_selecionado,
        'mes_selecionado': mes_selecionado,
        'anos_disponiveis': anos_disponiveis,
        'meses': meses,
    }
    return render(request, 'financeiro/metas_vendas.html', context)


@login_required
def despesas_operacionais(request):
    """Gestão de despesas operacionais."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Filtros
    status = request.GET.get('status', 'todas')
    tipo = request.GET.get('tipo', 'todas')
    recorrente = request.GET.get('recorrente', 'todas')
    
    # Filtrar despesas
    despesas = DespesaOperacional.objects.filter(pizzaria=pizzaria)
    
    if status == 'pagas':
        despesas = despesas.filter(pago=True)
    elif status == 'pendentes':
        despesas = despesas.filter(pago=False)
    
    if tipo != 'todas':
        despesas = despesas.filter(tipo=tipo)
    
    if recorrente == 'recorrentes':
        despesas = despesas.filter(recorrente=True)
    elif recorrente == 'nao_recorrentes':
        despesas = despesas.filter(recorrente=False)
    
    # Calcular totais
    total_pendente = despesas.filter(pago=False).aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    total_pendente = float(total_pendente) / 100
    
    total_pago = despesas.filter(pago=True).aggregate(
        total=Sum('valor_centavos')
    )['total'] or 0
    total_pago = float(total_pago) / 100
    
    # Contar despesas por status
    pendentes_count = despesas.filter(pago=False).count()
    pagas_count = despesas.filter(pago=True).count()
    recorrentes_count = despesas.filter(recorrente=True).count()
    
    context = {
        'despesas': despesas,
        'filtro_status': status,
        'filtro_tipo': tipo,
        'filtro_recorrente': recorrente,
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'pendentes_count': pendentes_count,
        'pagas_count': pagas_count,
        'recorrentes_count': recorrentes_count,
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
            
            # Se for recorrente, gerar despesas mensais automaticamente
            if despesa.recorrente:
                despesas_criadas = despesa.gerar_despesas_pendentes()
                if despesas_criadas:
                    messages.success(
                        request, 
                        f'Despesa fixa mensal criada e {len(despesas_criadas)} despesas mensais geradas automaticamente!'
                    )
                else:
                    messages.success(request, 'Despesa fixa mensal criada com sucesso!')
            else:
                messages.success(request, 'Despesa adicionada com sucesso!')
            
            return redirect('financeiro:despesas_operacionais')
        else:
            messages.error(request, 'Erro ao adicionar despesa. Verifique os campos.')
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
    despesa = get_object_or_404(
        DespesaOperacional, 
        id=despesa_id, 
        pizzaria=pizzaria
    )
    
    if request.method == 'POST':
        form = DespesaOperacionalForm(request.POST, instance=despesa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despesa atualizada com sucesso!')
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
    despesa = get_object_or_404(
        DespesaOperacional, 
        id=despesa_id, 
        pizzaria=pizzaria
    )
    
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
    despesa = get_object_or_404(
        DespesaOperacional, 
        id=despesa_id, 
        pizzaria=pizzaria
    )
    
    if request.method == 'POST':
        data_pagamento = request.POST.get('data_pagamento')
        if data_pagamento:
            try:
                data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
            except ValueError:
                data_pagamento = timezone.now().date()
        else:
            data_pagamento = timezone.now().date()
        
        despesa.marcar_como_paga(data_pagamento)
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
