from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
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
    produtos = Produto.objects.filter(pizzaria=pizzaria, disponivel=True).order_by('nome')

    context = {
        "pedidos": pedidos,
        "produtos_disponiveis": produtos,
        "status_choices": Pedido.STATUS_CHOICES,
    }
    return render(request, "pedidos/lista_pedidos.html", context)


@login_required
def alterar_status_pedido(request, pedido_id):
    """Altera o status de um pedido via AJAX."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and pedido.pizzaria != usuario_pizzaria.pizzaria:
        return JsonResponse({"error": "Permissão negada"}, status=403)
    
    novo_status = request.POST.get("status")
    if not novo_status:
        return JsonResponse({"error": "Status é obrigatório"}, status=400)
    
    # Validar se o status é válido
    status_validos = [choice[0] for choice in Pedido.STATUS_CHOICES]
    if novo_status not in status_validos:
        return JsonResponse({"error": "Status inválido"}, status=400)
    
    # Atualizar status
    pedido.status = novo_status
    pedido.save(update_fields=['status', 'data_atualizacao'])
    
    # Obter o nome do status para exibição
    status_display = dict(Pedido.STATUS_CHOICES)[novo_status]
    
    return JsonResponse({
        "success": True,
        "status": novo_status,
        "status_display": status_display,
        "message": f"Status do pedido #{pedido.id} alterado para {status_display}"
    })


@login_required
def detalhes_pedido(request, pedido_id):
    """Retorna detalhes do pedido em JSON para o modal."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and pedido.pizzaria != usuario_pizzaria.pizzaria:
        return JsonResponse({"error": "Permissão negada"}, status=403)
    
    # Preparar dados do pedido
    itens = []
    for item in pedido.itens.select_related('produto').all():
        itens.append({
            'produto_nome': item.produto.nome,
            'quantidade': item.quantidade,
            'valor_unitario': str(item.valor_unitario),
            'subtotal': str(item.subtotal),
            'observacao': item.observacao_item or ''
        })
    
    dados = {
        'id': pedido.id,
        'cliente_nome': pedido.cliente_nome or 'Cliente não informado',
        'cliente_telefone': pedido.cliente_telefone or '',
        'data_criacao': pedido.data_criacao.strftime('%d/%m/%Y às %H:%M'),
        'status': pedido.get_status_display(),
        'forma_pagamento': pedido.get_forma_pagamento_display(),
        'observacoes': pedido.observacoes or '',
        'total': str(pedido.total),
        'itens': itens
    }
    
    return JsonResponse(dados)


@login_required
def cancelar_pedido(request, pedido_id):
    """Cancela um pedido."""
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and pedido.pizzaria != usuario_pizzaria.pizzaria:
        return JsonResponse({"error": "Permissão negada"}, status=403)
    
    # Verificar se pode cancelar
    if pedido.status in ['ENTREGUE', 'CANCELADO']:
        return JsonResponse({"error": f"Não é possível cancelar pedido {pedido.get_status_display().lower()}"}, status=400)
    
    # Cancelar pedido
    pedido.status = 'CANCELADO'
    pedido.save(update_fields=['status', 'data_atualizacao'])
    
    return JsonResponse({
        "success": True,
        "message": f"Pedido #{pedido.id} cancelado com sucesso"
    })


@login_required
def editar_pedido(request, pedido_id):
    """Edita um pedido existente."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar permissão
    if not usuario_pizzaria.is_super_admin() and pedido.pizzaria != usuario_pizzaria.pizzaria:
        return JsonResponse({"error": "Permissão negada"}, status=403)
    
    # Verificar se pode editar
    if pedido.status in ['ENTREGUE', 'CANCELADO']:
        return JsonResponse({"error": f"Não é possível editar pedido {pedido.get_status_display().lower()}"}, status=400)
    
    if request.method == "POST":
        try:
            # Atualizar dados básicos do pedido
            pedido.cliente_nome = request.POST.get("cliente_nome", "")
            pedido.cliente_telefone = request.POST.get("cliente_telefone", "")
            pedido.forma_pagamento = request.POST.get("forma_pagamento")
            pedido.observacoes = request.POST.get("observacoes", "")
            
            # Validar forma de pagamento
            if not pedido.forma_pagamento:
                return JsonResponse({"error": "Forma de pagamento é obrigatória"}, status=400)
            
            pedido.save()
            
            # Remover itens existentes
            pedido.itens.all().delete()
            
            # Adicionar novos itens
            pizzaria = pedido.pizzaria
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
            
            return JsonResponse({
                "success": True,
                "message": f"Pedido #{pedido.id} atualizado com sucesso!"
            })
            
        except Exception as e:
            return JsonResponse({"error": f"Erro ao salvar pedido: {str(e)}"}, status=400)
    
    # GET - retornar dados para edição
    itens = []
    for item in pedido.itens.select_related('produto').all():
        itens.append({
            'produto_id': item.produto.id,
            'produto_nome': item.produto.nome,
            'quantidade': item.quantidade,
            'observacao': item.observacao_item or ''
        })
    
    produtos_disponiveis = []
    for produto in Produto.objects.filter(pizzaria=pedido.pizzaria, disponivel=True):
        produtos_disponiveis.append({
            'id': produto.id,
            'nome': produto.nome,
            'preco': float(produto.preco_atual)
        })
    
    dados = {
        'id': pedido.id,
        'cliente_nome': pedido.cliente_nome or '',
        'cliente_telefone': pedido.cliente_telefone or '',
        'forma_pagamento': pedido.forma_pagamento,
        'observacoes': pedido.observacoes or '',
        'itens': itens,
        'produtos_disponiveis': produtos_disponiveis
    }
    
    return JsonResponse(dados)
