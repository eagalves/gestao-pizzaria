from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, F
from django.utils import timezone
from decimal import Decimal

from autenticacao.decorators import super_admin_required
from autenticacao.models import Pizzaria
from ingredientes.models import Ingrediente
from .models import Fornecedor, EstoqueIngrediente, CompraIngrediente, HistoricoPrecoCompra
from .forms import FornecedorForm, CompraIngredienteForm, EstoqueIngredienteForm
from autenticacao.decorators import pizzaria_required


@pizzaria_required
def dashboard_estoque(request):
    """Dashboard principal do estoque."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Estatísticas gerais
    total_ingredientes = EstoqueIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria
    ).count()
    
    ingredientes_baixo_estoque = EstoqueIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        quantidade_atual__lte=F('estoque_minimo')
    ).count()
    
    valor_total_estoque = EstoqueIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria
    ).aggregate(
        total=Sum(F('quantidade_atual') * F('preco_compra_atual_centavos'))
    )['total'] or 0
    
    # Últimas compras
    ultimas_compras = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria
    ).select_related('ingrediente', 'fornecedor').order_by('-data_compra')[:5]
    
    # Ingredientes com estoque baixo
    estoque_baixo = EstoqueIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria,
        quantidade_atual__lte=F('estoque_minimo')
    ).select_related('ingrediente')[:10]
    
    context = {
        'total_ingredientes': total_ingredientes,
        'ingredientes_baixo_estoque': ingredientes_baixo_estoque,
        'valor_total_estoque': valor_total_estoque / 100,  # Converter para reais
        'ultimas_compras': ultimas_compras,
        'estoque_baixo': estoque_baixo,
    }
    
    return render(request, 'estoque/dashboard.html', context)


@pizzaria_required
def lista_estoque(request, pizzaria_id=None):
    """Lista todos os ingredientes em estoque."""
    # Se super_admin e pizzaria_id fornecido, usar essa pizzaria
    if pizzaria_id and request.user.usuarios_pizzaria.filter(ativo=True, papel='super_admin').exists():
        try:
            pizzaria = Pizzaria.objects.get(id=pizzaria_id)
        except Pizzaria.DoesNotExist:
            messages.error(request, 'Pizzaria não encontrada.')
            return redirect('estoque:lista_estoque')
    else:
        # Usar pizzaria do usuário logado
        pizzaria = request.user.usuarios_pizzaria.first().pizzaria
        
        # Se pizzaria_id foi fornecido mas usuário não é super_admin, redirecionar
        if pizzaria_id and pizzaria.id != pizzaria_id:
            messages.warning(request, 'Acesso restrito. Você só pode visualizar o estoque de sua própria pizzaria.')
            return redirect('estoque:lista_estoque')
    
    # Filtros
    busca = request.GET.get('busca', '')
    filtro_estoque = request.GET.get('filtro_estoque', 'todos')
    
    estoques = EstoqueIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria
    ).select_related('ingrediente')
    if busca:
        estoques = estoques.filter(
            Q(ingrediente__nome__icontains=busca)
        )
    
    if filtro_estoque == 'baixo':
        estoques = estoques.filter(quantidade_atual__lte=F('estoque_minimo'))
    elif filtro_estoque == 'zerado':
        estoques = estoques.filter(quantidade_atual=0)
    
    estoques = estoques.order_by('ingrediente__nome')
    
    context = {
        'estoques': estoques,
        'busca': busca,
        'filtro_estoque': filtro_estoque,
        'pizzaria_atual': pizzaria,
        'is_super_admin': request.user.usuarios_pizzaria.filter(ativo=True, papel='super_admin').exists(),
    }
    
    return render(request, 'estoque/lista_estoque.html', context)


@pizzaria_required
def editar_estoque(request, estoque_id):
    """Edita configurações de estoque de um ingrediente."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    estoque = get_object_or_404(
        EstoqueIngrediente, 
        id=estoque_id,
        ingrediente__pizzaria=pizzaria
    )
    
    if request.method == 'POST':
        form = EstoqueIngredienteForm(request.POST, instance=estoque)
        if form.is_valid():
            form.save()
            messages.success(request, 'Estoque atualizado com sucesso!')
            return redirect('estoque:lista_estoque')
    else:
        form = EstoqueIngredienteForm(instance=estoque)
    
    context = {
        'form': form,
        'estoque': estoque,
    }
    
    return render(request, 'estoque/editar_estoque.html', context)


def lista_fornecedores(request):
    """Lista todos os fornecedores."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    busca = request.GET.get('busca', '')
    
    fornecedores = Fornecedor.objects.filter(pizzaria=pizzaria)
    
    if busca:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=busca) |
            Q(cnpj__icontains=busca)
        )
    
    fornecedores = fornecedores.order_by('nome')
    
    context = {
        'fornecedores': fornecedores,
        'busca': busca,
    }
    
    return render(request, 'estoque/lista_fornecedores.html', context)


def adicionar_fornecedor(request):
    """Adiciona novo fornecedor."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save(commit=False)
            fornecedor.pizzaria = pizzaria
            fornecedor.save()
            messages.success(request, 'Fornecedor adicionado com sucesso!')
            return redirect('estoque:lista_fornecedores')
    else:
        form = FornecedorForm()
    
    context = {
        'form': form,
        'titulo': 'Adicionar Fornecedor'
    }
    
    return render(request, 'estoque/form_fornecedor.html', context)


def editar_fornecedor(request, fornecedor_id):
    """Edita fornecedor."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado com sucesso!')
            return redirect('estoque:lista_fornecedores')
    else:
        form = FornecedorForm(instance=fornecedor)
    
    context = {
        'form': form,
        'fornecedor': fornecedor,
        'titulo': 'Editar Fornecedor'
    }
    
    return render(request, 'estoque/form_fornecedor.html', context)


@pizzaria_required
def lista_compras(request):
    """Lista histórico de compras."""
    usuario_pizzaria = request.user.usuarios_pizzaria.first()
    if not usuario_pizzaria or not usuario_pizzaria.pizzaria:
        messages.error(request, 'Usuário não tem pizzaria associada.')
        return redirect('autenticacao:dashboard')
    
    pizzaria = usuario_pizzaria.pizzaria
    
    # Filtros
    busca = request.GET.get('busca', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Buscar compras para ingredientes desta pizzaria
    compras = CompraIngrediente.objects.filter(
        ingrediente__pizzaria=pizzaria
    ).select_related('ingrediente', 'fornecedor')
    
    if busca:
        compras = compras.filter(
            Q(ingrediente__nome__icontains=busca) |
            Q(fornecedor__nome__icontains=busca)
        )
    
    if data_inicio:
        compras = compras.filter(data_compra__gte=data_inicio)
    
    if data_fim:
        compras = compras.filter(data_compra__lte=data_fim)
    
    compras = compras.order_by('-data_compra')
    
    # Totais
    total_compras = compras.aggregate(
        total=Sum('valor_total_centavos')
    )['total'] or 0
    
    context = {
        'compras': compras,
        'busca': busca,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_compras': total_compras / 100,  # Converter para reais
    }
    
    return render(request, 'estoque/lista_compras.html', context)


def registrar_compra(request):
    """Registra nova compra de ingrediente."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    if request.method == 'POST':
        form = CompraIngredienteForm(request.POST, pizzaria=pizzaria)
        if form.is_valid():
            compra = form.save()
            messages.success(request, f'Compra de {compra.ingrediente.nome} registrada com sucesso!')
            return redirect('estoque:lista_compras')
    else:
        form = CompraIngredienteForm(pizzaria=pizzaria)
    
    context = {
        'form': form,
        'titulo': 'Registrar Compra'
    }
    
    return render(request, 'estoque/form_compra.html', context)


def historico_precos(request, ingrediente_id):
    """Mostra histórico de preços de um ingrediente."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id, pizzaria=pizzaria)
    
    historico = HistoricoPrecoCompra.objects.filter(
        ingrediente=ingrediente
    ).order_by('-data_preco')
    
    # Estatísticas
    if historico.exists():
        preco_medio = historico.aggregate(
            media=Sum('preco_centavos')
        )['media'] / historico.count()
        
        preco_minimo = min(h.preco_centavos for h in historico)
        preco_maximo = max(h.preco_centavos for h in historico)
    else:
        preco_medio = preco_minimo = preco_maximo = 0
    
    context = {
        'ingrediente': ingrediente,
        'historico': historico,
        'preco_medio': preco_medio / 100,
        'preco_minimo': preco_minimo / 100,
        'preco_maximo': preco_maximo / 100,
    }
    
    return render(request, 'estoque/historico_precos.html', context)


def relatorio_custos(request):
    """Relatório de custos dos produtos."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    
    # Buscar todos os produtos da pizzaria
    from produtos.models import Produto
    
    produtos = Produto.objects.filter(pizzaria=pizzaria).prefetch_related(
        'produto_ingredientes__ingrediente__estoque'
    )
    
    # Recalcular custos de todos os produtos
    for produto in produtos:
        produto.recalcular_custo()
    
    # Buscar preços atualizados
    produtos_com_precos = []
    for produto in produtos:
        preco_atual = produto.preco_atual
        if preco_atual:
            produtos_com_precos.append({
                'produto': produto,
                'preco_base': preco_atual.preco_base,
                'preco_custo': preco_atual.preco_custo,
                'preco_venda': preco_atual.preco_venda,
                'margem': preco_atual.margem_percentual,
                'lucro': preco_atual.lucro,
            })
    
    # Ordenar por margem (menor para maior)
    produtos_com_precos.sort(key=lambda x: x['margem'])
    
    context = {
        'produtos': produtos_com_precos,
    }
    
    return render(request, 'estoque/relatorio_custos.html', context)


@pizzaria_required
def ajax_ingrediente_preco(request, ingrediente_id):
    """Retorna preço atual do ingrediente via AJAX."""
    try:
        ingrediente = Ingrediente.objects.get(id=ingrediente_id)
        estoque = ingrediente.estoque
        return JsonResponse({
            'success': True,
            'preco_centavos': estoque.preco_compra_atual_centavos,
            'preco_reais': estoque.preco_compra_atual,
        })
    except:
        return JsonResponse({
            'success': False,
            'preco_centavos': 0,
            'preco_reais': 0,
        })
