from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def lista_produtos(request):
    """Exibe a tela de produtos; lista vazia nesta etapa inicial."""
    context = {
        "produtos": []
    }
    return render(request, "produtos/lista_produtos.html", context)
