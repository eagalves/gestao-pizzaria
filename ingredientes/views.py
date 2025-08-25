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
            # Se for super_admin, usar a primeira pizzaria disponível
            if usuario_pizzaria.is_super_admin():
                from autenticacao.models import Pizzaria
                primeira_pizzaria = Pizzaria.objects.first()
                if primeira_pizzaria:
                    ingrediente.pizzaria = primeira_pizzaria
                else:
                    messages.error(request, "Não há pizzarias cadastradas no sistema.")
                    return redirect('lista_ingredientes')
            else:
                # Para donos de pizzaria, usar a pizzaria do usuário
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

    # Buscar ingredientes baseado no papel do usuário
    if usuario_pizzaria.is_super_admin():
        # Super admin vê todos os ingredientes de todas as pizzarias
        ingredientes = Ingrediente.objects.all().select_related('pizzaria')
    else:
        # Dono de pizzaria vê apenas os ingredientes da sua pizzaria
        ingredientes = Ingrediente.objects.filter(pizzaria=usuario_pizzaria.pizzaria)
    
    context = {
        'ingredientes': ingredientes,
        'form': form,
        'is_super_admin': usuario_pizzaria.is_super_admin()
    }
    return render(request, "ingredientes/lista_ingredientes.html", context)


@login_required
def editar_ingrediente(request, ingrediente_id):
    """Edita um ingrediente existente."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id)

    # Verifica se o usuário tem permissão sobre esse ingrediente
    if not usuario_pizzaria.is_super_admin() and ingrediente.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_ingredientes")

    if request.method == "POST":
        form = IngredienteForm(request.POST, instance=ingrediente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ingrediente '{ingrediente.nome}' atualizado com sucesso!")
            return redirect("lista_ingredientes")
        else:
            messages.error(request, "Erro ao atualizar ingrediente. Verifique os dados.")
    else:
        form = IngredienteForm(instance=ingrediente)

    context = {
        "form": form,
        "ingrediente": ingrediente,
    }
    return render(request, "ingredientes/editar_ingrediente.html", context)


@login_required
def excluir_ingrediente(request, ingrediente_id):
    """Exclui um ingrediente após confirmação."""
    usuario_pizzaria = get_object_or_404(UsuarioPizzaria, usuario=request.user, ativo=True)
    ingrediente = get_object_or_404(Ingrediente, id=ingrediente_id)

    if not usuario_pizzaria.is_super_admin() and ingrediente.pizzaria != usuario_pizzaria.pizzaria:
        messages.error(request, "Permissão negada.")
        return redirect("lista_ingredientes")

    # Excluir diretamente e redirecionar
    ingrediente.delete()
    messages.success(request, f"Ingrediente '{ingrediente.nome}' excluído com sucesso!")
    return redirect("lista_ingredientes")
