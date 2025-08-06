from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

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

    produtos = Produto.objects.filter(pizzaria=pizzaria).select_related('categoria')

    ingredientes_disponiveis = Ingrediente.objects.filter(pizzaria=pizzaria)
    
    context = {
        'produtos': produtos,
        'form': form,
        'ingredientes_disponiveis': ingredientes_disponiveis,
    }
    return render(request, 'produtos/lista_produtos.html', context)
