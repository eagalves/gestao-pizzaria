from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator

from autenticacao.models import UsuarioPizzaria
from .models import Cliente, EnderecoCliente
from .forms import ClienteForm, EnderecoClienteForm


@login_required
def lista_clientes(request):
    """Lista clientes da pizzaria com busca e paginação."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    
    # Busca
    busca = request.GET.get('busca', '')
    clientes = Cliente.objects.filter(pizzaria=pizzaria, ativo=True)
    
    if busca:
        clientes = clientes.filter(
            Q(nome__icontains=busca) |
            Q(telefone__icontains=busca) |
            Q(email__icontains=busca)
        )
    
    # Ordenação
    clientes = clientes.select_related('endereco_principal').prefetch_related('pedidos')
    clientes = clientes.order_by('nome')
    
    # Paginação
    paginator = Paginator(clientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Processar cadastro via modal
    if request.method == 'POST':
        form = ClienteForm(request.POST, pizzaria=pizzaria)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.pizzaria = pizzaria
            cliente.save()
            
            # Verificar se foi enviado endereço
            endereco_nome = request.POST.get('endereco_nome', '').strip()
            endereco_cep = request.POST.get('endereco_cep', '').strip()
            endereco_rua = request.POST.get('endereco_rua', '').strip()
            endereco_numero = request.POST.get('endereco_numero', '').strip()
            endereco_bairro = request.POST.get('endereco_bairro', '').strip()
            endereco_cidade = request.POST.get('endereco_cidade', '').strip()
            endereco_estado = request.POST.get('endereco_estado', '').strip()
            
            # Se tem dados básicos de endereço, criar o endereço
            if endereco_nome and endereco_cep and endereco_rua and endereco_numero and endereco_bairro and endereco_cidade and endereco_estado:
                endereco = EnderecoCliente.objects.create(
                    cliente=cliente,
                    nome=endereco_nome,
                    cep=endereco_cep,
                    rua=endereco_rua,
                    numero=endereco_numero,
                    complemento=request.POST.get('endereco_complemento', '').strip(),
                    bairro=endereco_bairro,
                    cidade=endereco_cidade,
                    estado=endereco_estado,
                    referencia=request.POST.get('endereco_referencia', '').strip()
                )
                
                # Definir como endereço principal
                cliente.endereco_principal = endereco
                cliente.save()
                
                messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso! Endereço "{endereco.nome}" também foi cadastrado.')
            else:
                messages.success(request, f'Cliente "{cliente.nome}" cadastrado com sucesso!')
            
            return redirect('lista_clientes')
        else:
            messages.error(request, 'Erro ao cadastrar cliente. Verifique os dados.')
    else:
        form = ClienteForm(pizzaria=pizzaria)
    
    context = {
        'clientes': page_obj,
        'form': form,
        'busca': busca,
        'total_clientes': clientes.count() if not busca else Cliente.objects.filter(pizzaria=pizzaria, ativo=True).count(),
    }
    
    return render(request, 'clientes/lista_clientes.html', context)


@login_required
def detalhes_cliente(request, cliente_id):
    """Retorna detalhes do cliente em JSON para modal."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    cliente = get_object_or_404(Cliente, id=cliente_id, pizzaria=pizzaria)
    
    # Buscar TODOS os pedidos do cliente
    todos_pedidos = cliente.pedidos.order_by('-data_criacao')
    
    # Estatísticas atualizadas
    stats = {
        'total_pedidos': cliente.total_pedidos(),
        'total_gasto': cliente.total_gasto(),
        'ticket_medio': cliente.ticket_medio(),
        'ultimo_pedido': cliente.ultimo_pedido(),
        'pedidos_por_status': cliente.pedidos_por_status()
    }
    
    data = {
        'id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone,
        'email': cliente.email,
        'data_nascimento': cliente.data_nascimento.strftime('%d/%m/%Y') if cliente.data_nascimento else '',
        'observacoes': cliente.observacoes,
        'data_cadastro': cliente.data_cadastro.strftime('%d/%m/%Y às %H:%M'),
        'endereco_principal': cliente.endereco_principal.endereco_completo() if cliente.endereco_principal else 'Nenhum endereço cadastrado',
        'stats': {
            'total_pedidos': stats['total_pedidos'],
            'total_gasto': f"R$ {stats['total_gasto']:.2f}",
            'ticket_medio': f"R$ {stats['ticket_medio']:.2f}",
            'ultimo_pedido': stats['ultimo_pedido'].data_criacao.strftime('%d/%m/%Y às %H:%M') if stats['ultimo_pedido'] else 'Nunca',
            'pedidos_por_status': {item['status']: item['count'] for item in stats['pedidos_por_status']}
        },
        'todos_pedidos': [{
            'id': pedido.id,
            'data': pedido.data_criacao.strftime('%d/%m/%Y'),
            'hora': pedido.data_criacao.strftime('%H:%M'),
            'data_completa': pedido.data_criacao.strftime('%d/%m/%Y às %H:%M'),
            'total': f"R$ {pedido.total:.2f}",
            'total_raw': float(pedido.total),
            'status': pedido.status,
            'status_display': pedido.get_status_display(),
            'forma_pagamento': pedido.get_forma_pagamento_display(),
            'observacoes': pedido.observacoes or '',
            'itens_count': pedido.itens.count()
        } for pedido in todos_pedidos],
        'enderecos': [{
            'id': endereco.id,
            'nome': endereco.nome,
            'endereco': endereco.endereco_completo()
        } for endereco in cliente.enderecos.all()]
    }
    
    return JsonResponse(data)


@login_required
def editar_cliente(request, cliente_id):
    """Edita um cliente existente."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    cliente = get_object_or_404(Cliente, id=cliente_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente, pizzaria=pizzaria)
        if form.is_valid():
            cliente_atualizado = form.save()
            
            # Se for requisição AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'Cliente "{cliente_atualizado.nome}" atualizado com sucesso!',
                    'cliente': {
                        'id': cliente_atualizado.id,
                        'nome': cliente_atualizado.nome,
                        'telefone': cliente_atualizado.telefone,
                        'email': cliente_atualizado.email or '',
                    }
                })
            
            messages.success(request, f'Cliente "{cliente_atualizado.nome}" atualizado com sucesso!')
            return redirect('lista_clientes')
        else:
            # Se for requisição AJAX, retornar erro em JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Erro ao atualizar cliente. Verifique os dados.',
                    'errors': form.errors
                }, status=400)
            
            messages.error(request, 'Erro ao atualizar cliente. Verifique os dados.')
    else:
        form = ClienteForm(instance=cliente, pizzaria=pizzaria)
    
    context = {
        'form': form,
        'cliente': cliente,
        'enderecos': cliente.enderecos.all()
    }
    
    return render(request, 'clientes/editar_cliente.html', context)


@login_required
def excluir_cliente(request, cliente_id):
    """Exclui (desativa) um cliente."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    cliente = get_object_or_404(Cliente, id=cliente_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        # Soft delete - apenas desativa
        cliente.ativo = False
        cliente.save()
        
        messages.success(request, f'Cliente "{cliente.nome}" removido com sucesso!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


# ==================== VIEWS DE ENDEREÇOS ====================

@login_required
def adicionar_endereco(request, cliente_id):
    """Adiciona um novo endereço para o cliente."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    cliente = get_object_or_404(Cliente, id=cliente_id, pizzaria=pizzaria)
    
    if request.method == 'POST':
        form = EnderecoClienteForm(request.POST)
        if form.is_valid():
            endereco = form.save(commit=False)
            endereco.cliente = cliente
            endereco.save()
            
            # Se é o primeiro endereço, define como principal
            if not cliente.endereco_principal:
                cliente.endereco_principal = endereco
                cliente.save()
            
            # Se for requisição AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'Endereço "{endereco.nome}" adicionado com sucesso!',
                    'endereco': {
                        'id': endereco.id,
                        'nome': endereco.nome,
                        'endereco_completo': endereco.endereco_completo()
                    }
                })
            
            messages.success(request, f'Endereço "{endereco.nome}" adicionado com sucesso!')
            return redirect('editar_cliente', cliente_id=cliente.id)
        else:
            # Se for requisição AJAX, retornar erro em JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': 'Erro ao adicionar endereço. Verifique os dados.',
                    'errors': form.errors
                }, status=400)
            
            messages.error(request, 'Erro ao adicionar endereço. Verifique os dados.')
    else:
        form = EnderecoClienteForm()
    
    context = {
        'form': form,
        'cliente': cliente
    }
    
    return render(request, 'clientes/adicionar_endereco.html', context)


@login_required
def editar_endereco(request, endereco_id):
    """Edita um endereço existente."""
    endereco = get_object_or_404(EnderecoCliente, id=endereco_id)
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    
    # Verifica se o endereço pertence à pizzaria do usuário
    if endereco.cliente.pizzaria != pizzaria:
        messages.error(request, 'Endereço não encontrado.')
        return redirect('lista_clientes')
    
    if request.method == 'POST':
        form = EnderecoClienteForm(request.POST, instance=endereco)
        if form.is_valid():
            form.save()
            messages.success(request, f'Endereço "{endereco.nome}" atualizado com sucesso!')
            return redirect('editar_cliente', cliente_id=endereco.cliente.id)
        else:
            messages.error(request, 'Erro ao atualizar endereço. Verifique os dados.')
    else:
        form = EnderecoClienteForm(instance=endereco)
    
    context = {
        'form': form,
        'endereco': endereco,
        'cliente': endereco.cliente
    }
    
    return render(request, 'clientes/editar_endereco.html', context)


@login_required
def excluir_endereco(request, endereco_id):
    """Exclui um endereço do cliente."""
    endereco = get_object_or_404(EnderecoCliente, id=endereco_id)
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    
    # Verifica se o endereço pertence à pizzaria do usuário
    if endereco.cliente.pizzaria != pizzaria:
        return JsonResponse({'success': False, 'error': 'Endereço não encontrado'})
    
    if request.method == 'POST':
        cliente = endereco.cliente
        
        # Se é o endereço principal, remove a referência
        if cliente.endereco_principal == endereco:
            # Define outro endereço como principal se houver
            outro_endereco = cliente.enderecos.exclude(id=endereco.id).first()
            cliente.endereco_principal = outro_endereco
            cliente.save()
        
        endereco.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


@login_required
def definir_endereco_principal(request, endereco_id):
    """Define um endereço como principal."""
    endereco = get_object_or_404(EnderecoCliente, id=endereco_id)
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    
    # Verifica se o endereço pertence à pizzaria do usuário
    if endereco.cliente.pizzaria != pizzaria:
        return JsonResponse({'success': False, 'error': 'Endereço não encontrado'})
    
    if request.method == 'POST':
        cliente = endereco.cliente
        cliente.endereco_principal = endereco
        cliente.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})


# ==================== API PARA INTEGRAÇÃO COM PEDIDOS ====================

@login_required
def buscar_clientes(request):
    """API para buscar clientes (usado no sistema de pedidos)."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    pizzaria = usuario_pizzaria.pizzaria
    termo = request.GET.get('termo', '')
    
    if len(termo) < 2:
        return JsonResponse({'clientes': []})
    
    clientes = Cliente.objects.filter(
        pizzaria=pizzaria,
        ativo=True
    ).filter(
        Q(nome__icontains=termo) |
        Q(telefone__icontains=termo)
    )[:10]
    
    data = {
        'clientes': [{
            'id': cliente.id,
            'nome': cliente.nome,
            'telefone': cliente.telefone,
            'endereco_principal': cliente.endereco_principal.endereco_completo() if cliente.endereco_principal else '',
            'total_pedidos': cliente.total_pedidos(),
            'total_gasto': cliente.total_gasto()
        } for cliente in clientes]
    }
    
    return JsonResponse(data)