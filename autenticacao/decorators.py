from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UsuarioPizzaria


def pizzaria_required(view_func):
    """Decorator que garante acesso apenas a usuários autenticados com vínculo ativo em uma pizzaria.

    Uso:
        @pizzaria_required
        def minha_view(request):
            ...
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Usuário não autenticado
        if not request.user.is_authenticated:
            messages.error(request, "É necessário estar autenticado para acessar esta página.")
            return redirect("login")

        # Verificar se existe vínculo ativo
        usuario_pizzaria = (
            UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
        )

        if not usuario_pizzaria:
            messages.error(request, "Usuário sem perfil ativo no sistema. Entre em contato com o administrador.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def super_admin_required(view_func):
    """Decorator que garante acesso apenas a usuários com papel *Super Admin*.

    Uso:
        @login_required  # se desejar manter
        @super_admin_required
        def minha_view(request):
            ...
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Usuário não autenticado
        if not request.user.is_authenticated:
            messages.error(request, "É necessário estar autenticado para acessar esta página.")
            return redirect("login")

        # Verificar se existe vínculo ativo e se é super admin
        usuario_pizzaria = (
            UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
        )

        if not usuario_pizzaria:
            messages.error(request, "Usuário sem perfil ativo no sistema. Entre em contato com o administrador.")
            return redirect("dashboard")
        
        if not usuario_pizzaria.is_super_admin():
            messages.warning(request, "Acesso restrito. Apenas Super Administradores podem acessar esta funcionalidade.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
