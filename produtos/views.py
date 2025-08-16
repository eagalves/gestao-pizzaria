from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse

from autenticacao.models import UsuarioPizzaria
from ingredientes.models import Ingrediente
from .models import Produto, PrecoProduto, ProdutoIngrediente
from .forms import ProdutoForm


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
            PrecoProduto.objects.create(produto=produto, valor=form.cleaned_data['preco_base'])

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
            if novo_preco != produto.preco_atual:
                # Finaliza preço anterior
                PrecoProduto.objects.filter(produto=produto, data_fim__isnull=True).update(data_fim=timezone.now())
                PrecoProduto.objects.create(produto=produto, valor=novo_preco)

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
