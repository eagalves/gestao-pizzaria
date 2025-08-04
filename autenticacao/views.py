from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UsuarioPizzaria

def login_view(request):
    """Página de login do sistema"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Autenticar usuário
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar se usuário tem perfil no sistema
            usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=user, ativo=True).first()
            
            if usuario_pizzaria:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
                
                # Redirecionar baseado no papel
                if usuario_pizzaria.is_super_admin():
                    return redirect('dashboard_super_admin')
                elif usuario_pizzaria.is_dono_pizzaria():
                    return redirect('boas_vindas_pizzaria')
                else:
                    return redirect('dashboard')  # Fallback
            else:
                messages.error(request, 'Usuário não tem permissão para acessar o sistema.')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'autenticacao/login.html')

def logout_view(request):
    """Logout do sistema"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('login')

@login_required
def dashboard(request):
    """Dashboard padrão - redireciona conforme o papel"""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
    
    if not usuario_pizzaria:
        messages.error(request, 'Usuário sem permissões no sistema.')
        return redirect('login')
    
    if usuario_pizzaria.is_super_admin():
        return redirect('dashboard_super_admin')
    elif usuario_pizzaria.is_dono_pizzaria():
        return redirect('boas_vindas_pizzaria')
    
    # Fallback para casos inesperados
    messages.error(request, 'Papel de usuário não reconhecido.')
    return redirect('login')
