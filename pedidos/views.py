from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from autenticacao.models import UsuarioPizzaria
from produtos.models import Produto
from .models import Pedido, ItemPedido
from django.contrib import messages

@login_required
def lista_pedidos(request):
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria

    if request.method == "POST":
        # Criação do pedido
        cliente_nome = request.POST.get("cliente_nome", "")
        cliente_telefone = request.POST.get("cliente_telefone", "")
        forma_pagamento = request.POST.get("forma_pagamento")
        observacoes = request.POST.get("observacoes", "")

        if not forma_pagamento:
            messages.error(request, "Forma de pagamento é obrigatória.")
            return redirect("lista_pedidos")

        pedido = Pedido.objects.create(
            pizzaria=pizzaria,
            cliente_nome=cliente_nome,
            cliente_telefone=cliente_telefone,
            forma_pagamento=forma_pagamento,
            observacoes=observacoes,
            status="RECEBIDO",
        )

        # Processar itens
        for key, value in request.POST.items():
            if key.startswith("item_produto_") and value:
                idx = key.split("_")[2]
                produto_id = value
                qtd = int(request.POST.get(f"item_qtd_{idx}", 1))
                obs_item = request.POST.get(f"item_obs_{idx}", "")

                try:
                    produto = Produto.objects.get(id=produto_id, pizzaria=pizzaria)
                except Produto.DoesNotExist:
                    continue

                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=produto,
                    quantidade=qtd,
                    valor_unitario=produto.preco_atual,
                    observacao_item=obs_item,
                )
        # Atualizar total
        pedido.atualizar_total()
        messages.success(request, f"Pedido #{pedido.id} criado com sucesso!")
        return redirect("lista_pedidos")

    # GET - listar
    pedidos = Pedido.objects.filter(pizzaria=pizzaria).select_related("pizzaria").prefetch_related("itens__produto")
    produtos = Produto.objects.filter(pizzaria=pizzaria, disponivel=True)

    context = {
        "pedidos": pedidos,
        "produtos_disponiveis": produtos,
    }
    return render(request, "pedidos/lista_pedidos.html", context)
