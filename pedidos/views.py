from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from autenticacao.models import UsuarioPizzaria
from produtos.models import Produto

@login_required
def lista_pedidos(request):
    """Tela inicial de pedidos (somente front-end)."""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
    produtos = []
    if usuario_pizzaria:
        produtos = Produto.objects.filter(pizzaria=usuario_pizzaria.pizzaria)

    context = {
        "pedidos": [],  # nenhum pedido por enquanto
        "produtos_disponiveis": produtos,
    }
    return render(request, "pedidos/lista_pedidos.html", context)
