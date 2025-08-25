from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.db import transaction
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from autenticacao.models import Pizzaria, UsuarioPizzaria
from .models import Ingrediente
from .forms import IngredienteForm


class IngredienteModelTest(TransactionTestCase):
    """Testes para o modelo Ingrediente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
        
        self.ingrediente = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo mussarela tradicional",
            vegetariano=True,
            vegano=False,
            contem_gluten=False,
            contem_lactose=True
        )
    
    def test_criacao_ingrediente(self):
        """Testa se um ingrediente pode ser criado corretamente"""
        self.assertEqual(self.ingrediente.nome, "Queijo Mussarela")
        self.assertEqual(self.ingrediente.pizzaria, self.pizzaria)
        self.assertTrue(self.ingrediente.vegetariano)
        self.assertFalse(self.ingrediente.vegano)
        self.assertFalse(self.ingrediente.contem_gluten)
        self.assertTrue(self.ingrediente.contem_lactose)
    
    def test_str_representation(self):
        """Testa a representação string do ingrediente"""
        expected = f"Queijo Mussarela ({self.pizzaria.nome})"
        self.assertEqual(str(self.ingrediente), expected)
    
    def test_meta_verbose_names(self):
        """Testa os nomes verbosos do modelo"""
        self.assertEqual(Ingrediente._meta.verbose_name, "Ingrediente")
        self.assertEqual(Ingrediente._meta.verbose_name_plural, "Ingredientes")
    
    def test_ordering(self):
        """Testa se a ordenação está funcionando corretamente"""
        ingrediente2 = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Abacaxi",
            descricao="Abacaxi em rodelas"
        )
        
        ingredientes = Ingrediente.objects.all()
        self.assertEqual(ingredientes[0].nome, "Abacaxi")
        self.assertEqual(ingredientes[1].nome, "Queijo Mussarela")
    
    def test_unique_together_constraint(self):
        """Testa se a restrição de unicidade está funcionando"""
        # Tenta criar outro ingrediente com o mesmo nome para a mesma pizzaria
        with self.assertRaises(Exception):
            Ingrediente.objects.create(
                pizzaria=self.pizzaria,
                nome="Queijo Mussarela",  # Mesmo nome
                descricao="Outro queijo"
            )
        
        # Deve permitir ingredientes com o mesmo nome em pizzarias diferentes
        with transaction.atomic():
            pizzaria2 = Pizzaria.objects.create(
                nome="Pizzaria Teste 2",
                cnpj="98765432000110",
                telefone="(11) 88888-8888",
                endereco="Rua Teste 2, 456"
            )
            
            ingrediente2 = Ingrediente.objects.create(
                pizzaria=pizzaria2,
                nome="Queijo Mussarela",  # Mesmo nome, pizzaria diferente
                descricao="Queijo da pizzaria 2"
            )
            
            self.assertIsNotNone(ingrediente2.id)


class IngredienteFormTest(TestCase):
    """Testes para o formulário IngredienteForm"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
    
    def test_form_valido(self):
        """Testa se o formulário é válido com dados corretos"""
        form_data = {
            'nome': 'Tomate',
            'descricao': 'Tomate fresco',
            'vegetariano': True,
            'vegano': True,
            'contem_gluten': False,
            'contem_lactose': False
        }
        
        form = IngredienteForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_sem_nome(self):
        """Testa se o formulário é inválido sem nome"""
        form_data = {
            'descricao': 'Descrição sem nome',
            'vegetariano': True
        }
        
        form = IngredienteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_form_campos_obrigatorios(self):
        """Testa se apenas o nome é obrigatório"""
        form_data = {
            'nome': 'Ingrediente Simples'
        }
        
        form = IngredienteForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_campos_booleanos_padrao(self):
        """Testa se os campos booleanos têm valores padrão corretos"""
        form_data = {
            'nome': 'Ingrediente Teste'
        }
        
        form = IngredienteForm(data=form_data)
        if form.is_valid():
            ingrediente = form.save(commit=False)
            self.assertFalse(ingrediente.vegetariano)
            self.assertFalse(ingrediente.vegano)
            self.assertFalse(ingrediente.contem_gluten)
            self.assertFalse(ingrediente.contem_lactose)


class IngredienteViewsTest(TestCase):
    """Testes para as views do app ingredientes"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        
        # Criar usuário e pizzaria
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
        
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            ativo=True
        )
        
        self.ingrediente = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo mussarela tradicional"
        )
    
    def test_lista_ingredientes_get(self):
        """Testa o GET da view lista_ingredientes"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ingredientes/lista_ingredientes.html')
        self.assertIn('ingredientes', response.context)
        self.assertIn('form', response.context)
        self.assertIn(self.ingrediente, response.context['ingredientes'])
    
    def test_lista_ingredientes_post_valido(self):
        """Testa o POST da view lista_ingredientes com dados válidos"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Novo Ingrediente',
            'descricao': 'Descrição do novo ingrediente',
            'vegetariano': True
        }
        
        response = self.client.post(reverse('lista_ingredientes'), form_data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        self.assertTrue(Ingrediente.objects.filter(nome='Novo Ingrediente').exists())
        
        # Verifica se a mensagem de sucesso foi criada
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Novo Ingrediente' salvo com sucesso!")
    
    def test_lista_ingredientes_post_invalido(self):
        """Testa o POST da view lista_ingredientes com dados inválidos"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': '',  # Nome vazio
            'descricao': 'Descrição sem nome'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), form_data)
        
        self.assertEqual(response.status_code, 200)  # Retorna para o formulário
        self.assertFalse(Ingrediente.objects.filter(descricao='Descrição sem nome').exists())
        
        # Verifica se a mensagem de erro foi criada
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Houve um erro no formulário. Verifique os dados.")
    
    def test_lista_ingredientes_duplicado(self):
        """Testa o POST da view lista_ingredientes com nome duplicado"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Queijo Mussarela',  # Nome já existe
            'descricao': 'Outro queijo'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), form_data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verifica se a mensagem de erro foi criada
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Já existe um ingrediente com o nome 'Queijo Mussarela'.")
    
    def test_editar_ingrediente_get(self):
        """Testa o GET da view editar_ingrediente"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': self.ingrediente.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ingredientes/editar_ingrediente.html')
        self.assertIn('form', response.context)
        self.assertIn('ingrediente', response.context)
    
    def test_editar_ingrediente_post_valido(self):
        """Testa o POST da view editar_ingrediente com dados válidos"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Queijo Mussarela Atualizado',
            'descricao': 'Descrição atualizada',
            'vegetariano': True
        }
        
        response = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': self.ingrediente.id}),
            form_data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verifica se o ingrediente foi atualizado
        self.ingrediente.refresh_from_db()
        self.assertEqual(self.ingrediente.nome, 'Queijo Mussarela Atualizado')
        self.assertEqual(self.ingrediente.descricao, 'Descrição atualizada')
        self.assertTrue(self.ingrediente.vegetariano)
        
        # Verifica se a mensagem de sucesso foi criada
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Queijo Mussarela Atualizado' atualizado com sucesso!")
    
    def test_editar_ingrediente_post_invalido(self):
        """Testa o POST da view editar_ingrediente com dados inválidos"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': '',  # Nome vazio
            'descricao': 'Descrição sem nome'
        }
        
        response = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': self.ingrediente.id}),
            form_data
        )
        
        self.assertEqual(response.status_code, 200)  # Retorna para o formulário
        
        # Verifica se a mensagem de erro foi criada
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Erro ao atualizar ingrediente. Verifique os dados.")
    
    def test_excluir_ingrediente(self):
        """Testa a view excluir_ingrediente"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': self.ingrediente.id})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verifica se o ingrediente foi excluído
        self.assertFalse(Ingrediente.objects.filter(id=self.ingrediente.id).exists())
        
        # Verifica se a mensagem de sucesso foi criada
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Queijo Mussarela' excluído com sucesso!")
    
    def test_acesso_nao_autenticado(self):
        """Testa se usuários não autenticados são redirecionados"""
        urls = [
            reverse('lista_ingredientes'),
            reverse('editar_ingrediente', kwargs={'ingrediente_id': 1}),
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': 1})
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirecionamento para login


class IngredienteListagemTest(TestCase):
    """Testes específicos para garantir que a listagem de ingredientes funcione corretamente"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        
        # Criar usuário e pizzaria
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
        
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel='dono_pizzaria',
            ativo=True
        )
    
    def test_lista_ingredientes_vazia(self):
        """Testa se a página mostra corretamente quando não há ingredientes cadastrados"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ingredientes/lista_ingredientes.html')
        
        # Verifica se o contexto está correto
        self.assertIn('ingredientes', response.context)
        self.assertIn('form', response.context)
        
        # Verifica se a lista está vazia
        self.assertEqual(len(response.context['ingredientes']), 0)
        
        # Verifica se a mensagem "Nenhum ingrediente cadastrado" aparece no HTML
        self.assertContains(response, "Nenhum ingrediente cadastrado")
    
    def test_lista_ingredientes_com_um_ingrediente(self):
        """Testa se a página mostra corretamente um ingrediente cadastrado"""
        self.client.login(username='testuser', password='testpass123')
        
        # Criar um ingrediente
        ingrediente = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo mussarela tradicional",
            vegetariano=True,
            vegano=False,
            contem_gluten=False,
            contem_lactose=True
        )
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o ingrediente aparece no contexto
        self.assertIn(ingrediente, response.context['ingredientes'])
        self.assertEqual(len(response.context['ingredientes']), 1)
        
        # Verifica se o nome do ingrediente aparece no HTML
        self.assertContains(response, "Queijo Mussarela")
        self.assertContains(response, "Queijo mussarela tradicional")
        
        # Verifica se as características marcadas aparecem como badges na tabela
        self.assertContains(response, "bg-success-light text-success")  # Badge vegetariano
        self.assertContains(response, "bg-primary-light text-primary")  # Badge lactose
        
        # Verifica se as características não marcadas não aparecem como badges
        # (mas os campos do formulário sempre mostram todos os labels)
        self.assertNotContains(response, "bg-info-light text-info")      # Badge vegano
        self.assertNotContains(response, "bg-warning-light text-warning")  # Badge glúten
    
    def test_lista_ingredientes_com_multiplos_ingredientes(self):
        """Testa se a página mostra corretamente múltiplos ingredientes cadastrados"""
        self.client.login(username='testuser', password='testpass123')
        
        # Criar múltiplos ingredientes
        ingrediente1 = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo mussarela tradicional",
            vegetariano=True,
            vegano=False,
            contem_gluten=False,
            contem_lactose=True
        )
        
        ingrediente2 = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Tomate",
            descricao="Tomate fresco",
            vegetariano=True,
            vegano=True,
            contem_gluten=False,
            contem_lactose=False
        )
        
        ingrediente3 = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Presunto",
            descricao="Presunto de porco",
            vegetariano=False,
            vegano=False,
            contem_gluten=False,
            contem_lactose=False
        )
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se todos os ingredientes aparecem no contexto
        ingredientes_context = response.context['ingredientes']
        self.assertEqual(len(ingredientes_context), 3)
        self.assertIn(ingrediente1, ingredientes_context)
        self.assertIn(ingrediente2, ingredientes_context)
        self.assertIn(ingrediente3, ingredientes_context)
        
        # Verifica se todos os nomes aparecem no HTML
        self.assertContains(response, "Queijo Mussarela")
        self.assertContains(response, "Tomate")
        self.assertContains(response, "Presunto")
        
        # Verifica se as características aparecem corretamente
        self.assertContains(response, "Vegetariano")  # Queijo e Tomate
        self.assertContains(response, "Vegano")       # Apenas Tomate
        self.assertContains(response, "Lactose")      # Apenas Queijo
    
    def test_lista_ingredientes_apenas_da_pizzaria_do_usuario(self):
        """Testa se a página mostra apenas ingredientes da pizzaria do usuário logado"""
        self.client.login(username='testuser', password='testpass123')
        
        # Criar ingrediente para a pizzaria do usuário
        ingrediente_usuario = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo da pizzaria do usuário",
            vegetariano=True
        )
        
        # Criar outra pizzaria com ingrediente
        pizzaria_outra = Pizzaria.objects.create(
            nome="Pizzaria Outra",
            cnpj="11111111000111",
            telefone="(11) 77777-7777",
            endereco="Rua Outra, 999"
        )
        
        ingrediente_outra_pizzaria = Ingrediente.objects.create(
            pizzaria=pizzaria_outra,
            nome="Queijo Provolone",
            descricao="Queijo de outra pizzaria",
            vegetariano=True
        )
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se apenas o ingrediente da pizzaria do usuário aparece
        ingredientes_context = response.context['ingredientes']
        self.assertEqual(len(ingredientes_context), 1)
        self.assertIn(ingrediente_usuario, ingredientes_context)
        self.assertNotIn(ingrediente_outra_pizzaria, ingredientes_context)
        
        # Verifica se o nome correto aparece no HTML
        self.assertContains(response, "Queijo Mussarela")
        self.assertNotContains(response, "Queijo Provolone")
    
    def test_lista_ingredientes_ordenacao_alfabetica(self):
        """Testa se os ingredientes aparecem em ordem alfabética"""
        self.client.login(username='testuser', password='testpass123')
        
        # Criar ingredientes em ordem não alfabética
        ingrediente_c = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Cebola",
            descricao="Cebola roxa"
        )
        
        ingrediente_a = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Abacaxi",
            descricao="Abacaxi em rodelas"
        )
        
        ingrediente_b = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Bacon",
            descricao="Bacon frito"
        )
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se os ingredientes estão em ordem alfabética
        ingredientes_context = response.context['ingredientes']
        self.assertEqual(len(ingredientes_context), 3)
        self.assertEqual(ingredientes_context[0].nome, "Abacaxi")
        self.assertEqual(ingredientes_context[1].nome, "Bacon")
        self.assertEqual(ingredientes_context[2].nome, "Cebola")
    
    def test_lista_ingredientes_formulario_presente(self):
        """Testa se o formulário para adicionar ingrediente está presente na página"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o formulário está no contexto
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], IngredienteForm)
        
        # Verifica se o botão "Novo Ingrediente" está presente
        self.assertContains(response, "Novo Ingrediente")
        
        # Verifica se o modal está presente
        self.assertContains(response, "modalNovoIngrediente")
    
    def test_lista_ingredientes_acoes_para_cada_ingrediente(self):
        """Testa se cada ingrediente tem botões de ação (editar/excluir)"""
        self.client.login(username='testuser', password='testpass123')
        
        # Criar um ingrediente
        ingrediente = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo mussarela tradicional"
        )
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se os botões de ação estão presentes
        self.assertContains(response, "fas fa-edit")  # Ícone de editar
        self.assertContains(response, "fas fa-trash-alt")  # Ícone de excluir
        
        # Verifica se os links de ação estão presentes
        self.assertContains(response, f'data-id="{ingrediente.id}"')
        self.assertContains(response, f'data-nome="{ingrediente.nome}"')
        self.assertContains(response, f'data-descricao="{ingrediente.descricao}"')


class IngredienteAPITest(APITestCase):
    """Testes para as APIs do app ingredientes"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
        
        # Criar usuário associado à pizzaria
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel='dono_pizzaria',
            ativo=True
        )
        
        self.ingrediente = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Queijo Mussarela",
            descricao="Queijo mussarela tradicional"
        )
    
    def test_lista_ingredientes_api_get(self):
        """Testa a API GET para listar ingredientes"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/v1/ingredientes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ingredientes', response.data)
        self.assertEqual(len(response.data['ingredientes']), 1)
        
        ingrediente_data = response.data['ingredientes'][0]
        self.assertEqual(ingrediente_data['nome'], 'Queijo Mussarela')
        self.assertEqual(ingrediente_data['descricao'], 'Queijo mussarela tradicional')
        self.assertFalse(ingrediente_data['vegetariano'])
        self.assertFalse(ingrediente_data['vegano'])
        self.assertFalse(ingrediente_data['contem_gluten'])
        self.assertFalse(ingrediente_data['contem_lactose'])
    
    def test_lista_ingredientes_api_sem_autenticacao(self):
        """Testa se a API requer autenticação"""
        response = self.client.get('/api/v1/ingredientes/')
        
        # Pode retornar 401 (Unauthorized) ou 403 (Forbidden) para usuários não autenticados
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_criar_ingrediente_api_post(self):
        """Testa a API POST para criar ingrediente"""
        self.client.force_authenticate(user=self.user)
        
        ingrediente_data = {
            'nome': 'Novo Ingrediente API',
            'descricao': 'Ingrediente criado via API',
            'vegetariano': True,
            'vegano': False,
            'contem_gluten': False,
            'contem_lactose': True
        }
        
        response = self.client.post('/api/v1/ingredientes/criar/', ingrediente_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('ingrediente', response.data)
        
        # Verifica se o ingrediente foi criado no banco
        self.assertTrue(Ingrediente.objects.filter(nome='Novo Ingrediente API').exists())
        
        # Verifica se os dados retornados estão corretos
        ingrediente_retornado = response.data['ingrediente']
        self.assertEqual(ingrediente_retornado['nome'], 'Novo Ingrediente API')
        self.assertEqual(ingrediente_retornado['descricao'], 'Ingrediente criado via API')
        self.assertTrue(ingrediente_retornado['vegetariano'])
        self.assertFalse(ingrediente_retornado['vegano'])
        self.assertFalse(ingrediente_retornado['contem_gluten'])
        self.assertTrue(ingrediente_retornado['contem_lactose'])
    
    def test_criar_ingrediente_api_dados_invalidos(self):
        """Testa a API POST com dados inválidos"""
        self.client.force_authenticate(user=self.user)
        
        ingrediente_data = {
            'nome': '',  # Nome vazio
            'descricao': 'Descrição sem nome'
        }
        
        response = self.client.post('/api/v1/ingredientes/criar/', ingrediente_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
    
    def test_detalhes_ingrediente_api_get(self):
        """Testa a API GET para detalhes do ingrediente"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/v1/ingredientes/{self.ingrediente.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ingrediente', response.data)
        
        ingrediente_data = response.data['ingrediente']
        self.assertEqual(ingrediente_data['id'], self.ingrediente.id)
        self.assertEqual(ingrediente_data['nome'], 'Queijo Mussarela')
        self.assertEqual(ingrediente_data['descricao'], 'Queijo mussarela tradicional')
        self.assertFalse(ingrediente_data['vegetariano'])
        self.assertFalse(ingrediente_data['vegano'])
        self.assertFalse(ingrediente_data['contem_gluten'])
        self.assertFalse(ingrediente_data['contem_lactose'])
    
    def test_detalhes_ingrediente_api_nao_encontrado(self):
        """Testa a API GET para ingrediente inexistente"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/v1/ingredientes/999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Ingrediente não encontrado')


class IngredienteIntegrationTest(TransactionTestCase):
    """Testes de integração para o app ingredientes"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        
        # Criar usuário e pizzaria
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
        
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            ativo=True
        )
    
    def test_fluxo_completo_ingrediente(self):
        """Testa o fluxo completo de criação, edição e exclusão de ingrediente"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Criar ingrediente
        form_data = {
            'nome': 'Ingrediente Teste',
            'descricao': 'Descrição inicial',
            'vegetariano': True
        }
        
        response = self.client.post(reverse('lista_ingredientes'), form_data)
        self.assertEqual(response.status_code, 302)
        
        ingrediente = Ingrediente.objects.get(nome='Ingrediente Teste')
        self.assertIsNotNone(ingrediente)
        self.assertEqual(ingrediente.descricao, 'Descrição inicial')
        self.assertTrue(ingrediente.vegetariano)
        
        # 2. Editar ingrediente
        form_data_edicao = {
            'nome': 'Ingrediente Teste Atualizado',
            'descricao': 'Descrição atualizada',
            'vegetariano': False,
            'vegano': True
        }
        
        response = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': ingrediente.id}),
            form_data_edicao
        )
        self.assertEqual(response.status_code, 302)
        
        ingrediente.refresh_from_db()
        self.assertEqual(ingrediente.nome, 'Ingrediente Teste Atualizado')
        self.assertEqual(ingrediente.descricao, 'Descrição atualizada')
        self.assertFalse(ingrediente.vegetariano)
        self.assertTrue(ingrediente.vegano)
        
        # 3. Excluir ingrediente
        response = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': ingrediente.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # Verifica se foi excluído
        self.assertFalse(Ingrediente.objects.filter(id=ingrediente.id).exists())
    
    def test_validacoes_modelo(self):
        """Testa as validações do modelo em cenários reais"""
        # Testa criação com dados válidos
        ingrediente = Ingrediente.objects.create(
            pizzaria=self.pizzaria,
            nome="Ingrediente Válido",
            descricao="Descrição válida"
        )
        self.assertIsNotNone(ingrediente.id)
        
        # Testa que não pode criar com mesmo nome na mesma pizzaria
        with self.assertRaises(Exception):
            Ingrediente.objects.create(
                pizzaria=self.pizzaria,
                nome="Ingrediente Válido",  # Mesmo nome
                descricao="Outra descrição"
            )
        
        # Testa que pode criar com mesmo nome em pizzaria diferente
        with transaction.atomic():
            pizzaria2 = Pizzaria.objects.create(
                nome="Pizzaria Teste 2",
                cnpj="98765432000110",
                telefone="(11) 88888-8888",
                endereco="Rua Teste 2, 456"
            )
            
            ingrediente2 = Ingrediente.objects.create(
                pizzaria=pizzaria2,
                nome="Ingrediente Válido",  # Mesmo nome, pizzaria diferente
                descricao="Descrição da pizzaria 2"
            )
            self.assertIsNotNone(ingrediente2.id)
    
    def test_formulario_em_contexto(self):
        """Testa se o formulário está sendo passado corretamente no contexto"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], IngredienteForm)
        
        # Verifica se o formulário tem os campos corretos
        form = response.context['form']
        expected_fields = ['nome', 'descricao', 'vegetariano', 'vegano', 'contem_gluten', 'contem_lactose']
        for field in expected_fields:
            self.assertIn(field, form.fields)


class IngredienteEndToEndTest(TestCase):
    """Testes end-to-end para o app de ingredientes"""
    
    def setUp(self):
        """Configuração inicial para os testes E2E"""
        self.client = Client()
        
        # Criar usuário e pizzaria
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            telefone="(11) 99999-9999",
            endereco="Rua Teste, 123"
        )
        
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel='dono_pizzaria',
            ativo=True
        )
    
    def test_fluxo_basico_ingrediente_e2e(self):
        """Testa o fluxo básico de ingredientes end-to-end"""
        # 1. Login do usuário
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Acessar página inicial de ingredientes (deve estar vazia)
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum ingrediente cadastrado")
        
        # 3. Criar ingrediente via formulário
        ingrediente_data = {
            'nome': 'Queijo Mussarela',
            'descricao': 'Queijo mussarela tradicional',
            'vegetariano': True,
            'vegano': False,
            'contem_gluten': False,
            'contem_lactose': True
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # 4. Verificar se ingrediente foi criado e aparece na lista
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Queijo Mussarela")
        self.assertContains(response, "Queijo mussarela tradicional")
        self.assertContains(response, "Vegetariano")
        self.assertContains(response, "Lactose")
        
        # 5. Verificar se apenas um ingrediente existe
        self.assertEqual(len(response.context['ingredientes']), 1)
    
    def test_criacao_edicao_exclusao_e2e(self):
        """Testa criação, edição e exclusão de ingrediente end-to-end"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Criar ingrediente
        ingrediente_data = {
            'nome': 'Ingrediente Teste',
            'descricao': 'Para testar operações'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        self.assertEqual(response.status_code, 302)
        
        # 2. Verificar se foi criado
        ingrediente = Ingrediente.objects.get(nome='Ingrediente Teste')
        self.assertIsNotNone(ingrediente)
        
        # 3. Editar ingrediente
        edicao_data = {
            'nome': 'Ingrediente Editado',
            'descricao': 'Descrição editada'
        }
        
        response = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': ingrediente.id}),
            edicao_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar se foi editado
        ingrediente.refresh_from_db()
        self.assertEqual(ingrediente.nome, 'Ingrediente Editado')
        self.assertEqual(ingrediente.descricao, 'Descrição editada')
        
        # 5. Excluir ingrediente
        response = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': ingrediente.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # 6. Verificar se foi excluído
        self.assertFalse(Ingrediente.objects.filter(id=ingrediente.id).exists())
    
    def test_validacoes_e2e(self):
        """Testa validações end-to-end"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Tentar criar ingrediente sem nome
        ingrediente_invalido = {
            'nome': '',
            'descricao': 'Descrição sem nome'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_invalido)
        self.assertEqual(response.status_code, 200)  # Retorna para formulário
        
        # 2. Verificar se mensagem de erro aparece
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Houve um erro no formulário. Verifique os dados.")
        
        # 3. Criar ingrediente válido
        ingrediente_valido = {
            'nome': 'Ingrediente Válido',
            'descricao': 'Descrição válida'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_valido)
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar se ingrediente foi criado
        self.assertTrue(Ingrediente.objects.filter(nome='Ingrediente Válido').exists())
    
    def test_interface_e2e(self):
        """Testa interface end-to-end"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Verificar se todos os elementos da interface estão presentes
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos da interface
        self.assertContains(response, "Ingredientes")
        self.assertContains(response, "Gerencie os ingredientes disponíveis para seus produtos")
        self.assertContains(response, "Novo Ingrediente")
        self.assertContains(response, "modalNovoIngrediente")
        self.assertContains(response, "Nome")
        self.assertContains(response, "Descrição")
        self.assertContains(response, "Características")
        self.assertContains(response, "Ações")
        
        # 2. Criar ingrediente para testar ações
        ingrediente_data = {
            'nome': 'Ingrediente Teste',
            'descricao': 'Para testar ações'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Verificar se botões de ação aparecem
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        
        ingrediente = Ingrediente.objects.get(nome='Ingrediente Teste')
        self.assertContains(response, "fas fa-edit")
        self.assertContains(response, "fas fa-trash-alt")
        self.assertContains(response, f'data-id="{ingrediente.id}"')
        
        # 4. Testar acesso à página de edição
        response = self.client.get(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': ingrediente.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ingredientes/editar_ingrediente.html')
        self.assertContains(response, "Editar Ingrediente")
        self.assertContains(response, ingrediente.nome)
    
    def test_isolamento_usuarios_e2e(self):
        """Testa isolamento entre usuários end-to-end"""
        # 1. Criar segundo usuário com pizzaria diferente
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        pizzaria2 = Pizzaria.objects.create(
            nome="Pizzaria Teste 2",
            cnpj="98765432000110",
            telefone="(11) 88888-8888",
            endereco="Rua Teste 2, 456"
        )
        
        usuario_pizzaria2 = UsuarioPizzaria.objects.create(
            usuario=user2,
            pizzaria=pizzaria2,
            papel='dono_pizzaria',
            ativo=True
        )
        
        # 2. Usuário 1 cria ingrediente
        self.client.login(username='testuser', password='testpass123')
        ingrediente_data = {
            'nome': 'Ingrediente Usuário 1',
            'descricao': 'Só para usuário 1'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Usuário 2 cria ingrediente
        self.client.login(username='testuser2', password='testpass123')
        ingrediente2_data = {
            'nome': 'Ingrediente Usuário 2',
            'descricao': 'Só para usuário 2'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente2_data)
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar que usuário 2 só vê seu ingrediente
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingrediente Usuário 2")
        self.assertEqual(len(response.context['ingredientes']), 1)
        
        # 5. Usuário 1 só vê seu ingrediente
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingrediente Usuário 1")
        self.assertEqual(len(response.context['ingredientes']), 1)
    
    def test_ordenacao_e2e(self):
        """Testa ordenação end-to-end"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Criar múltiplos ingredientes em ordem não alfabética
        ingredientes_nomes = ['Zebra', 'Abacaxi', 'Banana', 'Cebola', 'Damasco']
        
        for nome in ingredientes_nomes:
            ingrediente_data = {
                'nome': nome,
                'descricao': f'Descrição de {nome}'
            }
            response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
            self.assertEqual(response.status_code, 302)
        
        # 2. Verificar se todos aparecem na lista
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ingredientes']), 5)
        
        # 3. Verificar ordenação alfabética
        ingredientes_context = response.context['ingredientes']
        nomes_ordenados = [ing.nome for ing in ingredientes_context]
        self.assertEqual(nomes_ordenados, ['Abacaxi', 'Banana', 'Cebola', 'Damasco', 'Zebra'])
        
        # 4. Verificar se todos os nomes aparecem no HTML
        for nome in ingredientes_nomes:
            self.assertContains(response, nome)
    
    def test_mensagens_sucesso_e2e(self):
        """Testa mensagens de sucesso end-to-end"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Criar ingrediente com sucesso
        ingrediente_data = {
            'nome': 'Ingrediente Sucesso',
            'descricao': 'Para testar mensagens'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Ingrediente Sucesso' salvo com sucesso!")
        
        # 2. Verificar se ingrediente aparece na lista
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingrediente Sucesso")
        self.assertEqual(len(response.context['ingredientes']), 1)


class SuperAdminIngredienteTest(TestCase):
    """Testes específicos para garantir que super_admins tenham acesso total a todas as funcionalidades"""
    
    def setUp(self):
        """Configuração inicial para os testes de super_admin"""
        self.client = Client()
        
        # Criar usuário super_admin
        self.super_admin_user = User.objects.create_user(
            username='superadmin',
            password='superpass123'
        )
        
        # Criar múltiplas pizzarias para testar acesso global
        self.pizzaria1 = Pizzaria.objects.create(
            nome="Pizzaria Alpha",
            cnpj="11111111000111",
            telefone="(11) 11111-1111",
            endereco="Rua Alpha, 111"
        )
        
        self.pizzaria2 = Pizzaria.objects.create(
            nome="Pizzaria Beta",
            cnpj="22222222000222",
            telefone="(11) 22222-2222",
            endereco="Rua Beta, 222"
        )
        
        self.pizzaria3 = Pizzaria.objects.create(
            nome="Pizzaria Gamma",
            cnpj="33333333000333",
            telefone="(11) 33333-3333",
            endereco="Rua Gamma, 333"
        )
        
        # Criar usuário super_admin sem pizzaria específica
        self.super_admin = UsuarioPizzaria.objects.create(
            usuario=self.super_admin_user,
            pizzaria=None,  # Super admin não tem pizzaria específica
            papel='super_admin',
            ativo=True
        )
        
        # Criar usuários donos de pizzaria para comparação
        self.dono_pizzaria1 = UsuarioPizzaria.objects.create(
            usuario=User.objects.create_user(username='dono1', password='dono123'),
            pizzaria=self.pizzaria1,
            papel='dono_pizzaria',
            ativo=True
        )
        
        self.dono_pizzaria2 = UsuarioPizzaria.objects.create(
            usuario=User.objects.create_user(username='dono2', password='dono123'),
            pizzaria=self.pizzaria2,
            papel='dono_pizzaria',
            ativo=True
        )
        
        # Criar ingredientes em diferentes pizzarias
        self.ingrediente_pizzaria1 = Ingrediente.objects.create(
            pizzaria=self.pizzaria1,
            nome="Queijo Alpha",
            descricao="Queijo da pizzaria Alpha",
            vegetariano=True,
            vegano=False,
            contem_gluten=False,
            contem_lactose=True
        )
        
        self.ingrediente_pizzaria2 = Ingrediente.objects.create(
            pizzaria=self.pizzaria2,
            nome="Tomate Beta",
            descricao="Tomate da pizzaria Beta",
            vegetariano=True,
            vegano=True,
            contem_gluten=False,
            contem_lactose=False
        )
        
        self.ingrediente_pizzaria3 = Ingrediente.objects.create(
            pizzaria=self.pizzaria3,
            nome="Carne Gamma",
            descricao="Carne da pizzaria Gamma",
            vegetariano=False,
            vegano=False,
            contem_gluten=False,
            contem_lactose=False
        )
    
    def test_super_admin_ve_todos_ingredientes(self):
        """Testa se super_admin vê todos os ingredientes de todas as pizzarias"""
        self.client.login(username='superadmin', password='superpass123')
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ingredientes/lista_ingredientes.html')
        
        # Verificar se todos os ingredientes estão no contexto
        ingredientes = response.context['ingredientes']
        self.assertEqual(len(ingredientes), 3)
        
        # Verificar se todos os ingredientes aparecem
        nomes_ingredientes = [ing.nome for ing in ingredientes]
        self.assertIn("Queijo Alpha", nomes_ingredientes)
        self.assertIn("Tomate Beta", nomes_ingredientes)
        self.assertIn("Carne Gamma", nomes_ingredientes)
        
        # Verificar se a coluna Pizzaria está sendo exibida
        self.assertContains(response, "Pizzaria")
        self.assertContains(response, "Pizzaria Alpha")
        self.assertContains(response, "Pizzaria Beta")
        self.assertContains(response, "Pizzaria Gamma")
    
    def test_super_admin_pode_criar_ingrediente_para_qualquer_pizzaria(self):
        """Testa se super_admin pode criar ingredientes para qualquer pizzaria"""
        self.client.login(username='superadmin', password='superpass123')
        
        # Criar ingrediente (será associado à primeira pizzaria disponível)
        ingrediente_data = {
            'nome': 'Novo Ingrediente Super Admin',
            'descricao': 'Criado por super admin',
            'vegetariano': True,
            'vegano': False,
            'contem_gluten': False,
            'contem_lactose': True
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verificar se o ingrediente foi criado
        novo_ingrediente = Ingrediente.objects.filter(nome='Novo Ingrediente Super Admin').first()
        self.assertIsNotNone(novo_ingrediente)
        
        # Verificar se foi associado a uma pizzaria (primeira disponível)
        self.assertIsNotNone(novo_ingrediente.pizzaria)
        self.assertIn(novo_ingrediente.pizzaria, [self.pizzaria1, self.pizzaria2, self.pizzaria3])
        
        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Novo Ingrediente Super Admin' salvo com sucesso!")
    
    def test_super_admin_pode_editar_qualquer_ingrediente(self):
        """Testa se super_admin pode editar ingredientes de qualquer pizzaria"""
        self.client.login(username='superadmin', password='superpass123')
        
        # Editar ingrediente da pizzaria 1
        form_data = {
            'nome': 'Queijo Alpha Atualizado',
            'descricao': 'Queijo atualizado por super admin',
            'vegetariano': True,
            'vegano': False,
            'contem_gluten': False,
            'contem_lactose': True
        }
        
        response = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': self.ingrediente_pizzaria1.id}),
            form_data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verificar se o ingrediente foi atualizado
        self.ingrediente_pizzaria1.refresh_from_db()
        self.assertEqual(self.ingrediente_pizzaria1.nome, 'Queijo Alpha Atualizado')
        self.assertEqual(self.ingrediente_pizzaria1.descricao, 'Queijo atualizado por super admin')
        
        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Queijo Alpha Atualizado' atualizado com sucesso!")
        
        # Editar ingrediente da pizzaria 2
        form_data2 = {
            'nome': 'Tomate Beta Atualizado',
            'descricao': 'Tomate atualizado por super admin',
            'vegetariano': True,
            'vegano': True,
            'contem_gluten': False,
            'contem_lactose': False
        }
        
        response2 = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': self.ingrediente_pizzaria2.id}),
            form_data2
        )
        
        self.assertEqual(response2.status_code, 302)
        
        # Verificar se o segundo ingrediente foi atualizado
        self.ingrediente_pizzaria2.refresh_from_db()
        self.assertEqual(self.ingrediente_pizzaria2.nome, 'Tomate Beta Atualizado')
    
    def test_super_admin_pode_excluir_qualquer_ingrediente(self):
        """Testa se super_admin pode excluir ingredientes de qualquer pizzaria"""
        self.client.login(username='superadmin', password='superpass123')
        
        # Excluir ingrediente da pizzaria 1
        response = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': self.ingrediente_pizzaria1.id})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verificar se o ingrediente foi excluído
        self.assertFalse(Ingrediente.objects.filter(id=self.ingrediente_pizzaria1.id).exists())
        
        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ingrediente 'Queijo Alpha' excluído com sucesso!")
        
        # Excluir ingrediente da pizzaria 2
        response2 = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': self.ingrediente_pizzaria2.id})
        )
        
        self.assertEqual(response2.status_code, 302)
        
        # Verificar se o segundo ingrediente foi excluído
        self.assertFalse(Ingrediente.objects.filter(id=self.ingrediente_pizzaria2.id).exists())
    
    def test_super_admin_acesso_negado_para_donos_pizzaria(self):
        """Testa se donos de pizzaria não conseguem acessar ingredientes de outras pizzarias"""
        # Testar com dono da pizzaria 1
        self.client.login(username='dono1', password='dono123')
        
        # Tentar editar ingrediente da pizzaria 2
        response = self.client.get(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': self.ingrediente_pizzaria2.id})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento por permissão negada
        
        # Verificar mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Permissão negada.")
        
        # Fazer logout e login novamente para limpar o contexto
        self.client.logout()
        self.client.login(username='dono1', password='dono123')
        
        # Tentar excluir ingrediente da pizzaria 2
        response2 = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': self.ingrediente_pizzaria2.id})
        )
        
        self.assertEqual(response2.status_code, 302)
        
        # Verificar mensagem de erro
        messages2 = list(get_messages(response2.wsgi_request))
        self.assertEqual(len(messages2), 1)
        self.assertEqual(str(messages2[0]), "Permissão negada.")
    
    def test_super_admin_context_variables(self):
        """Testa se as variáveis de contexto estão corretas para super_admin"""
        self.client.login(username='superadmin', password='superpass123')
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar variáveis de contexto
        context = response.context
        self.assertIn('ingredientes', context)
        self.assertIn('form', context)
        self.assertIn('is_super_admin', context)
        
        # Verificar se is_super_admin é True
        self.assertTrue(context['is_super_admin'])
        
        # Verificar se todos os ingredientes estão sendo exibidos
        ingredientes = context['ingredientes']
        self.assertEqual(len(ingredientes), 3)
    
    def test_super_admin_vs_dono_pizzaria_isolamento(self):
        """Testa se super_admin e donos de pizzaria veem ingredientes diferentes"""
        # Super admin vê todos os ingredientes
        self.client.login(username='superadmin', password='superpass123')
        response_super = self.client.get(reverse('lista_ingredientes'))
        
        ingredientes_super = response_super.context['ingredientes']
        self.assertEqual(len(ingredientes_super), 3)
        
        # Dono da pizzaria 1 vê apenas seus ingredientes
        self.client.login(username='dono1', password='dono123')
        response_dono1 = self.client.get(reverse('lista_ingredientes'))
        
        ingredientes_dono1 = response_dono1.context['ingredientes']
        self.assertEqual(len(ingredientes_dono1), 1)
        self.assertEqual(ingredientes_dono1[0].pizzaria, self.pizzaria1)
        
        # Dono da pizzaria 2 vê apenas seus ingredientes
        self.client.login(username='dono2', password='dono123')
        response_dono2 = self.client.get(reverse('lista_ingredientes'))
        
        ingredientes_dono2 = response_dono2.context['ingredientes']
        self.assertEqual(len(ingredientes_dono2), 1)
        self.assertEqual(ingredientes_dono2[0].pizzaria, self.pizzaria2)
    
    def test_super_admin_criacao_ingrediente_sem_pizzarias(self):
        """Testa comportamento quando não há pizzarias cadastradas"""
        # Excluir todas as pizzarias
        Pizzaria.objects.all().delete()
        
        self.client.login(username='superadmin', password='superpass123')
        
        # Tentar criar ingrediente
        ingrediente_data = {
            'nome': 'Ingrediente Sem Pizzaria',
            'descricao': 'Teste sem pizzarias'
        }
        
        response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verificar mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Não há pizzarias cadastradas no sistema.")
        
        # Verificar se o ingrediente não foi criado
        self.assertFalse(Ingrediente.objects.filter(nome='Ingrediente Sem Pizzaria').exists())
    
    def test_super_admin_manipulacao_em_lote(self):
        """Testa se super_admin pode manipular múltiplos ingredientes de diferentes pizzarias"""
        self.client.login(username='superadmin', password='superpass123')
        
        # Criar múltiplos ingredientes
        ingredientes_nomes = ['Ingrediente A', 'Ingrediente B', 'Ingrediente C']
        
        for nome in ingredientes_nomes:
            ingrediente_data = {
                'nome': nome,
                'descricao': f'Descrição de {nome}',
                'vegetariano': True
            }
            
            response = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
            self.assertEqual(response.status_code, 302)
        
        # Verificar se todos foram criados
        for nome in ingredientes_nomes:
            self.assertTrue(Ingrediente.objects.filter(nome=nome).exists())
        
        # Verificar se super_admin vê todos os ingredientes (incluindo os originais)
        response = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response.status_code, 200)
        
        ingredientes = response.context['ingredientes']
        self.assertEqual(len(ingredientes), 6)  # 3 originais + 3 novos
        
        # Verificar se todos os nomes aparecem
        nomes_ingredientes = [ing.nome for ing in ingredientes]
        for nome in ingredientes_nomes:
            self.assertIn(nome, nomes_ingredientes)
    
    def test_super_admin_permissoes_completas(self):
        """Testa se super_admin tem todas as permissões necessárias"""
        self.client.login(username='superadmin', password='superpass123')
        
        # 1. Pode ver lista de ingredientes
        response_lista = self.client.get(reverse('lista_ingredientes'))
        self.assertEqual(response_lista.status_code, 200)
        
        # 2. Pode criar ingredientes
        ingrediente_data = {
            'nome': 'Ingrediente Permissões',
            'descricao': 'Teste de permissões'
        }
        response_criar = self.client.post(reverse('lista_ingredientes'), ingrediente_data)
        self.assertEqual(response_criar.status_code, 302)
        
        # 3. Pode editar ingredientes
        novo_ingrediente = Ingrediente.objects.get(nome='Ingrediente Permissões')
        form_data = {
            'nome': 'Ingrediente Permissões Editado',
            'descricao': 'Editado por super admin'
        }
        response_editar = self.client.post(
            reverse('editar_ingrediente', kwargs={'ingrediente_id': novo_ingrediente.id}),
            form_data
        )
        self.assertEqual(response_editar.status_code, 302)
        
        # 4. Pode excluir ingredientes
        response_excluir = self.client.get(
            reverse('excluir_ingrediente', kwargs={'ingrediente_id': novo_ingrediente.id})
        )
        self.assertEqual(response_excluir.status_code, 302)
        
        # Verificar se foi excluído
        self.assertFalse(Ingrediente.objects.filter(nome='Ingrediente Permissões Editado').exists())
    
    def test_super_admin_interface_diferenciada(self):
        """Testa se a interface é diferenciada para super_admin"""
        self.client.login(username='superadmin', password='superpass123')
        response = self.client.get(reverse('lista_ingredientes'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se a coluna Pizzaria está sendo exibida
        self.assertContains(response, "Pizzaria")
        
        # Verificar se os nomes das pizzarias aparecem
        self.assertContains(response, "Pizzaria Alpha")
        self.assertContains(response, "Pizzaria Beta")
        self.assertContains(response, "Pizzaria Gamma")
        
        # Verificar se a coluna Pizzaria está sendo exibida
        self.assertContains(response, "Pizzaria")
        
        # Verificar se os nomes das pizzarias aparecem
        self.assertContains(response, "Pizzaria Alpha")
        self.assertContains(response, "Pizzaria Beta")
        self.assertContains(response, "Pizzaria Gamma")
        
        # Fazer login como dono de pizzaria para comparar
        self.client.login(username='dono1', password='dono123')
        response_dono = self.client.get(reverse('lista_ingredientes'))
        
        # Verificar se a coluna Pizzaria NÃO está sendo exibida para donos
        # (deve aparecer apenas no cabeçalho da tabela, não no conteúdo)
        self.assertNotContains(response_dono, '<th>Pizzaria</th>')
        
        # Verificar se o contexto está correto para donos
        self.assertIn('is_super_admin', response_dono.context)
        self.assertFalse(response_dono.context['is_super_admin'])
