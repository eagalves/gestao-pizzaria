from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from autenticacao.models import UsuarioPizzaria
from .models import Ingrediente
from .forms import IngredienteForm

@login_required
def lista_ingredientes(request):
    """
    Lista os ingredientes da pizzaria do usuário logado e processa
    o formulário de adição de um novo ingrediente.
    """
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    
    if request.method == 'POST':
        form = IngredienteForm(request.POST)
        if form.is_valid():
            ingrediente = form.save(commit=False)
            ingrediente.pizzaria = usuario_pizzaria.pizzaria
            try:
                ingrediente.save()
                messages.success(request, f"Ingrediente '{ingrediente.nome}' salvo com sucesso!")
            except Exception:
                messages.error(request, f"Já existe um ingrediente com o nome '{ingrediente.nome}'.")
            return redirect('lista_ingredientes')
        else:
            messages.error(request, "Houve um erro no formulário. Verifique os dados.")
    else:
        form = IngredienteForm()

    ingredientes = Ingrediente.objects.filter(pizzaria=usuario_pizzaria.pizzaria)
    
    context = {
        'ingredientes': ingredientes,
        'form': form
    }
    return render(request, "ingredientes/lista_ingredientes.html", context)
