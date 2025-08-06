from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UsuarioPizzaria, Pizzaria
from .forms import PizzariaForm

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


@login_required
def cadastro_pizzaria(request):
    """Cadastro de nova pizzaria (apenas Super Admin)"""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()

    if not usuario_pizzaria or not usuario_pizzaria.is_super_admin():
        messages.error(request, 'Permissão negada. Apenas Super Admin pode acessar.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = PizzariaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pizzaria cadastrada com sucesso!')
            return redirect('dashboard_super_admin')
    else:
        form = PizzariaForm()

    context = {
        'form': form,
    }
    return render(request, 'autenticacao/cadastro_pizzaria.html', context)


@login_required
def lista_pizzarias(request):
    """Lista completa de pizzarias (apenas Super Admin)"""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()

    if not usuario_pizzaria or not usuario_pizzaria.is_super_admin():
        messages.error(request, 'Permissão negada. Apenas Super Admin pode acessar.')
        return redirect('dashboard')

    pizzarias = Pizzaria.objects.all()
    context = {
        'pizzarias': pizzarias,
    }
    return render(request, 'autenticacao/lista_pizzarias.html', context)


@login_required
def dashboard_super_admin(request):
    """Dashboard para Super Admin"""
    usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()

    if not usuario_pizzaria or not usuario_pizzaria.is_super_admin():
        messages.error(request, 'Permissão negada. Apenas Super Admin pode acessar.')
        return redirect('dashboard')

    # Dados para o dashboard
    pizzarias = Pizzaria.objects.all()
    total_pizzarias = pizzarias.count()
    total_usuarios = UsuarioPizzaria.objects.count()
    total_super_admins = UsuarioPizzaria.objects.filter(papel='super_admin').count()
    total_donos = UsuarioPizzaria.objects.filter(papel='dono_pizzaria').count()

    context = {
        'pizzarias': pizzarias,
        'total_pizzarias': total_pizzarias,
        'total_usuarios': total_usuarios,
        'total_super_admins': total_super_admins,
        'total_donos': total_donos,
    }
    return render(request, 'autenticacao/dashboard_super_admin.html', context)
