from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse

from autenticacao.models import UsuarioPizzaria
from ingredientes.models import Ingrediente
from .models import Produto, PrecoProduto, ProdutoIngrediente, CategoriaProduto
from .forms import ProdutoForm, CategoriaForm, PrecoProdutoForm


@login_required
def lista_produtos(request):
    """Lista produtos da pizzaria e processa cadastro via modal."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria

    if request.method == 'POST':
        form = ProdutoForm(request.POST, pizzaria=pizzaria)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.pizzaria = pizzaria
            produto.save()

            # preço base
            preco_base = form.cleaned_data['preco_base']
            PrecoProduto.objects.create(
                produto=produto, 
                preco_base_centavos=int(preco_base * 100),
                preco_custo_centavos=0,  # Será calculado depois
                preco_venda_centavos=int(preco_base * 100),  # Inicialmente igual ao preço base
                data_inicio=timezone.now().date()
            )

            # Processar ingredientes enviados via formulário
            for key, value in request.POST.items():
                if key.startswith('ingrediente_') and value:
                    index = key.split('_')[1]
                    ingrediente_id = value
                    quantidade_key = f'quantidade_{index}'
                    unidade_key = f'unidade_{index}'
                    
                    if quantidade_key in request.POST and unidade_key in request.POST:
                        quantidade = request.POST[quantidade_key]
                        unidade = request.POST[unidade_key]
                        
                        try:
                            ingrediente = Ingrediente.objects.get(id=ingrediente_id, pizzaria=pizzaria)
                            ProdutoIngrediente.objects.create(
                                produto=produto,
                                ingrediente=ingrediente,
                                quantidade=quantidade,
                                unidade=unidade
                            )
                        except Ingrediente.DoesNotExist:
                            pass  # Ignora ingredientes inválidos

            messages.success(request, 'Produto salvo com sucesso!')
            return redirect('lista_produtos')
        else:
            messages.error(request, 'Erro ao salvar produto. Verifique os dados.')
    else:
        form = ProdutoForm(pizzaria=pizzaria)

    produtos = Produto.objects.filter(pizzaria=pizzaria).select_related('categoria').prefetch_related('produto_ingredientes__ingrediente')

    ingredientes_disponiveis = Ingrediente.objects.filter(pizzaria=pizzaria)
    
    context = {
        'produtos': produtos,
        'form': form,
        'ingredientes_disponiveis': ingredientes_disponiveis,
    }
    return render(request, 'produtos/lista_produtos.html', context)


@login_required
def editar_produto(request, produto_id):
    """Edita um produto existente (incluindo ingredientes)."""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
    if not usuario_pizzaria:
        messages.error(request, "Usuário sem permissões no sistema.")
        return redirect("login")

    produto = get_object_or_404(Produto, id=produto_id)

    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and produto.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_produtos")

    pizzaria = produto.pizzaria

    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto, pizzaria=pizzaria)
        if form.is_valid():
            produto = form.save()
            
            # Atualizar preço se mudou
            novo_preco = form.cleaned_data["preco_base"]
            preco_atual_obj = produto.preco_atual
            preco_atual_valor = preco_atual_obj.preco_base if preco_atual_obj else 0
            
            if novo_preco != preco_atual_valor:
                # Finaliza preço anterior
                PrecoProduto.objects.filter(produto=produto, data_fim__isnull=True).update(data_fim=timezone.now())
                # Criar novo preço
                PrecoProduto.objects.create(
                    produto=produto, 
                    preco_base_centavos=int(novo_preco * 100),
                    preco_custo_centavos=0,  # Será calculado depois
                    preco_venda_centavos=int(novo_preco * 100),  # Inicialmente igual ao preço base
                    data_inicio=timezone.now().date()
                )

            # Processar ingredientes - primeiro remover todos os existentes
            ProdutoIngrediente.objects.filter(produto=produto).delete()
            
            # Adicionar os novos ingredientes
            for key, value in request.POST.items():
                if key.startswith('ingrediente_') and value:
                    index = key.split('_')[1]
                    ingrediente_id = value
                    quantidade_key = f'quantidade_{index}'
                    unidade_key = f'unidade_{index}'
                    
                    if quantidade_key in request.POST and unidade_key in request.POST:
                        quantidade = request.POST[quantidade_key]
                        unidade = request.POST[unidade_key]
                        
                        try:
                            ingrediente = Ingrediente.objects.get(id=ingrediente_id, pizzaria=pizzaria)
                            ProdutoIngrediente.objects.create(
                                produto=produto,
                                ingrediente=ingrediente,
                                quantidade=quantidade,
                                unidade=unidade
                            )
                        except Ingrediente.DoesNotExist:
                            pass  # Ignora ingredientes inválidos

            messages.success(request, "Produto atualizado com sucesso!")
            return redirect("lista_produtos")
        else:
            messages.error(request, "Erro ao salvar alterações. Verifique os dados.")
    else:
        initial = {
            "preco_base": produto.preco_atual,
        }
        form = ProdutoForm(instance=produto, pizzaria=pizzaria, initial=initial)

    # Carregar ingredientes existentes do produto
    ingredientes_produto = produto.produto_ingredientes.select_related('ingrediente').all()
    ingredientes_disponiveis = Ingrediente.objects.filter(pizzaria=pizzaria)

    context = {
        "form": form,
        "produto": produto,
        "ingredientes_produto": ingredientes_produto,
        "ingredientes_disponiveis": ingredientes_disponiveis,
    }
    return render(request, "produtos/editar_produto.html", context)


@login_required
def ingredientes_produto(request, produto_id):
    """Retorna os ingredientes de um produto em formato JSON."""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
    if not usuario_pizzaria:
        return JsonResponse({"error": "Usuário sem permissões"}, status=403)

    produto = get_object_or_404(Produto, id=produto_id)

    if not usuario_pizzaria.is_super_admin() and produto.pizzaria != usuario_pizzaria.pizzaria:
        return JsonResponse({"error": "Permissão negada"}, status=403)

    ingredientes = []
    for pi in produto.produto_ingredientes.select_related('ingrediente').all():
        ingredientes.append({
            'ingrediente_id': pi.ingrediente.id,
            'ingrediente_nome': pi.ingrediente.nome,
            'quantidade': str(pi.quantidade),
            'unidade': pi.unidade
        })

    return JsonResponse({"ingredientes": ingredientes})


@login_required
def excluir_produto(request, produto_id):
    """Exclui um produto."""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
    if not usuario_pizzaria:
        messages.error(request, "Usuário sem permissões no sistema.")
        return redirect("login")

    produto = get_object_or_404(Produto, id=produto_id)

    if not usuario_pizzaria.is_super_admin() and produto.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_produtos")

    produto.delete()
    messages.success(request, "Produto excluído com sucesso!")
    return redirect("lista_produtos")


# ==================== DISPONIBILIDADE ====================

@login_required
def alternar_disponibilidade(request, produto_id):
    """Ativa ou desativa a disponibilidade de um produto (toggle)."""
    if request.method != "POST":
        return redirect("lista_produtos")

    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
    if not usuario_pizzaria:
        messages.error(request, "Usuário sem permissões no sistema.")
        return redirect("login")

    produto = get_object_or_404(Produto, id=produto_id)

    # Verificar permissão: super_admin ou dono da pizzaria
    if not usuario_pizzaria.is_super_admin() and produto.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_produtos")

    produto.disponivel = not produto.disponivel
    produto.save()

    estado = "disponível" if produto.disponivel else "indisponível"
    messages.success(request, f'Produto "{produto.nome}" marcado como {estado}.')
    return redirect("lista_produtos")


# ==================== VIEWS DE CATEGORIAS ====================

@login_required
def lista_categorias(request):
    """Lista categorias da pizzaria e processa cadastro via modal."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria

    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.pizzaria = pizzaria
            categoria.save()
            messages.success(request, f'Categoria "{categoria.nome}" criada com sucesso!')
            return redirect('lista_categorias')
        else:
            messages.error(request, 'Erro ao criar categoria. Verifique os dados.')
    else:
        form = CategoriaForm()

    categorias = CategoriaProduto.objects.filter(pizzaria=pizzaria).order_by('ordem', 'nome')
    
    # Estatísticas por categoria
    for categoria in categorias:
        categoria.total_produtos = categoria.produtos.count()

    context = {
        'categorias': categorias,
        'form': form,
    }
    return render(request, 'produtos/lista_categorias.html', context)


@login_required
def editar_categoria(request, categoria_id):
    """Edita uma categoria existente."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    categoria = get_object_or_404(CategoriaProduto, id=categoria_id)

    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and categoria.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_categorias")

    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoria "{categoria.nome}" atualizada com sucesso!')
            return redirect("lista_categorias")
        else:
            messages.error(request, "Erro ao salvar alterações. Verifique os dados.")
    else:
        form = CategoriaForm(instance=categoria)

    context = {
        "form": form,
        "categoria": categoria,
    }
    return render(request, "produtos/editar_categoria.html", context)


@login_required
def excluir_categoria(request, categoria_id):
    """Exclui uma categoria."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    categoria = get_object_or_404(CategoriaProduto, id=categoria_id)

    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and categoria.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_categorias")

    # Verificar se há produtos usando esta categoria
    produtos_count = categoria.produtos.count()
    if produtos_count > 0:
        messages.error(request, f'Não é possível excluir a categoria "{categoria.nome}" pois ela possui {produtos_count} produto(s) associado(s).')
        return redirect("lista_categorias")

    nome_categoria = categoria.nome
    categoria.delete()
    messages.success(request, f'Categoria "{nome_categoria}" excluída com sucesso!')
    return redirect("lista_categorias")


@login_required
def reordenar_categorias(request):
    """Reordena categorias via AJAX."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    
    try:
        # Receber lista de IDs na nova ordem
        categoria_ids = request.POST.getlist('categoria_ids[]')
        
        for index, categoria_id in enumerate(categoria_ids):
            CategoriaProduto.objects.filter(
                id=categoria_id, 
                pizzaria=pizzaria
            ).update(ordem=index)
        
        return JsonResponse({"success": True, "message": "Ordem das categorias atualizada!"})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def gerenciar_precos(request, produto_id):
    """Gerencia preços de um produto específico."""
    pizzaria = request.user.usuarios_pizzaria.first().pizzaria
    produto = get_object_or_404(Produto, id=produto_id, pizzaria=pizzaria)
    
    # Buscar ou criar preço atual
    preco_atual, created = PrecoProduto.objects.get_or_create(
        produto=produto,
        data_fim__isnull=True,
        defaults={
            'preco_base_centavos': 0,
            'preco_custo_centavos': 0,
            'preco_venda_centavos': 0,
            'data_inicio': timezone.now().date()
        }
    )
    
    if request.method == 'POST':
        form = PrecoProdutoForm(request.POST, instance=preco_atual)
        if form.is_valid():
            form.save()
            messages.success(request, f'Preços do produto "{produto.nome}" atualizados com sucesso!')
            return redirect('lista_produtos')
    else:
        form = PrecoProdutoForm(instance=preco_atual)
    
    context = {
        'produto': produto,
        'form': form,
        'preco_atual': preco_atual,
        'ingredientes': produto.get_ingredientes(),
    }
    
    return render(request, 'produtos/gerenciar_precos.html', context)
