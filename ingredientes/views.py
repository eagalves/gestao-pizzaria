from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def lista_ingredientes(request):
    """Exibe a página de ingredientes (apenas frontend)."""
    # Como não há banco de dados nesta etapa, passamos uma lista vazia.
    context = {
        "ingredientes": []
    }
    return render(request, "ingredientes/lista_ingredientes.html", context)
