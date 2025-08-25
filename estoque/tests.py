from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import json

from autenticacao.models import Pizzaria, UsuarioPizzaria
from ingredientes.models import Ingrediente
from .models import (
    Fornecedor, 
    EstoqueIngrediente, 
    CompraIngrediente, 
    HistoricoPrecoCompra
)
from .forms import FornecedorForm, CompraIngredienteForm, EstoqueIngredienteForm
from .views import dashboard_estoque, lista_estoque, editar_estoque


class EstoqueModelsTestCase(TestCase):
    """Testes para os modelos do módulo estoque."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar pizzaria
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            endereco="Rua Teste, 123",
            telefone="(11) 99999-9999"
        )
        
        # Criar usuário
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="teste@teste.com",
            password="testpass123"
        )
        
        # Criar usuário da pizzaria
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel="dono_pizzaria"
        )
        
        # Criar ingrediente
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo Mussarela",
            descricao="Queijo mussarela de búfala",
            pizzaria=self.pizzaria
        )
        
        # Criar fornecedor
        self.fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor Teste",
            cnpj="98765432000110",
            telefone="(11) 88888-8888",
            email="fornecedor@teste.com",
            ativo=True
        )

    def test_fornecedor_creation(self):
        """Testa criação de fornecedor."""
        fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Novo Fornecedor",
            cnpj="11111111000111"
        )
        
        self.assertEqual(fornecedor.nome, "Novo Fornecedor")
        self.assertEqual(fornecedor.pizzaria, self.pizzaria)
        self.assertTrue(fornecedor.ativo)
        self.assertIsNotNone(fornecedor.criado_em)

    def test_fornecedor_unique_together(self):
        """Testa que não pode haver fornecedores com mesmo nome na mesma pizzaria."""
        # Primeiro fornecedor já foi criado no setUp
        with self.assertRaises(Exception):
            Fornecedor.objects.create(
                pizzaria=self.pizzaria,
                nome="Fornecedor Teste",  # Mesmo nome
                cnpj="00000000000000"
            )

    def test_estoque_ingrediente_creation(self):
        """Testa criação de estoque de ingrediente."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('10.5'),
            estoque_minimo=Decimal('2.0'),
            estoque_maximo=Decimal('20.0'),
            unidade_medida='kg',
            preco_compra_atual_centavos=2550  # R$ 25,50
        )
        
        self.assertEqual(estoque.quantidade_atual, Decimal('10.5'))
        self.assertEqual(estoque.preco_compra_atual, Decimal('25.50'))
        self.assertFalse(estoque.estoque_baixo)
        self.assertEqual(estoque.valor_total_estoque, Decimal('267.75'))

    def test_estoque_baixo_detection(self):
        """Testa detecção de estoque baixo."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('1.0'),
            estoque_minimo=Decimal('2.0'),
            preco_compra_atual_centavos=1000
        )
        
        self.assertTrue(estoque.estoque_baixo)

    def test_estoque_preco_conversion(self):
        """Testa conversão de preço de centavos para reais."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('5.0'),
            preco_compra_atual_centavos=2550  # R$ 25,50
        )
        
        self.assertEqual(estoque.preco_compra_atual, Decimal('25.50'))

    def test_compra_ingrediente_creation(self):
        """Testa criação de compra de ingrediente."""
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            fornecedor=self.fornecedor,
            quantidade=Decimal('5.0'),
            unidade='kg',
            preco_unitario_centavos=2500,  # R$ 25,00/kg
            data_compra=date.today()
        )
        
        self.assertEqual(compra.quantidade, Decimal('5.0'))
        self.assertEqual(compra.preco_unitario, Decimal('25.00'))
        self.assertEqual(compra.valor_total, Decimal('125.00'))

    def test_compra_ingrediente_auto_calculation(self):
        """Testa cálculo automático do valor total na compra."""
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            fornecedor=self.fornecedor,
            quantidade=Decimal('3.0'),
            unidade='kg',
            preco_unitario_centavos=3000,  # R$ 30,00/kg
            data_compra=date.today()
        )
        
        # O valor total deve ser calculado automaticamente
        self.assertEqual(compra.valor_total_centavos, 9000)  # 3 * 3000
        self.assertEqual(compra.valor_total, Decimal('90.00'))

    def test_compra_ingrediente_update_estoque(self):
        """Testa que a compra atualiza automaticamente o estoque."""
        # Criar estoque inicial
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('0.0'),
            unidade_medida='kg',
            preco_compra_atual_centavos=0
        )
        
        # Registrar compra
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            fornecedor=self.fornecedor,
            quantidade=Decimal('10.0'),
            unidade='kg',
            preco_unitario_centavos=2000,  # R$ 20,00/kg
            data_compra=date.today()
        )
        
        # Recarregar estoque do banco
        estoque.refresh_from_db()
        
        # Verificar que o estoque foi atualizado
        self.assertEqual(estoque.quantidade_atual, Decimal('10.0'))
        self.assertEqual(estoque.preco_compra_atual_centavos, 2000)
        self.assertEqual(estoque.data_ultima_compra, date.today())

    def test_historico_preco_creation(self):
        """Testa criação de histórico de preços."""
        historico = HistoricoPrecoCompra.objects.create(
            ingrediente=self.ingrediente,
            preco_centavos=2500,
            data_preco=date.today(),
            fornecedor="Fornecedor Teste"
        )
        
        self.assertEqual(historico.preco_centavos, 2500)
        self.assertEqual(historico.preco, Decimal('25.00'))
        self.assertEqual(historico.fornecedor, "Fornecedor Teste")

    def test_compra_ingrediente_historico_preco(self):
        """Testa que a compra cria automaticamente histórico de preços."""
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            fornecedor=self.fornecedor,
            quantidade=Decimal('5.0'),
            unidade='kg',
            preco_unitario_centavos=2500,
            data_compra=date.today()
        )
        
        # Verificar se o histórico foi criado
        historico = HistoricoPrecoCompra.objects.filter(
            ingrediente=self.ingrediente,
            compra=compra
        ).first()
        
        self.assertIsNotNone(historico)
        self.assertEqual(historico.preco_centavos, 2500)
        self.assertEqual(historico.data_preco, date.today())


class EstoqueFormsTestCase(TestCase):
    """Testes para os formulários do módulo estoque."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            endereco="Rua Teste, 123"
        )
        
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo",
            pizzaria=self.pizzaria
        )
        
        self.fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor Teste"
        )

    def test_fornecedor_form_valid(self):
        """Testa formulário de fornecedor válido."""
        form_data = {
            'nome': 'Novo Fornecedor',
            'cnpj': '11.111.111/0001-11',
            'telefone': '(11) 99999-9999',
            'email': 'teste@fornecedor.com',
            'ativo': True
        }
        
        form = FornecedorForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_fornecedor_form_invalid(self):
        """Testa formulário de fornecedor inválido."""
        form_data = {
            'nome': '',  # Nome obrigatório
            'cnpj': 'cnpj-invalido'
        }
        
        form = FornecedorForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)

    def test_estoque_ingrediente_form_valid(self):
        """Testa formulário de estoque válido."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('10.0'),
            preco_compra_atual_centavos=2500
        )
        
        form_data = {
            'quantidade_atual': '15.0',
            'estoque_minimo': '5.0',
            'estoque_maximo': '25.0',
            'unidade_medida': 'kg',
            'preco_compra_reais': '30.00'
        }
        
        form = EstoqueIngredienteForm(data=form_data, instance=estoque)
        self.assertTrue(form.is_valid())

    def test_compra_ingrediente_form_unidade_valid(self):
        """Testa formulário de compra com unidade válido."""
        form_data = {
            'ingrediente': self.ingrediente.id,
            'fornecedor': self.fornecedor.id,
            'quantidade': '10',
            'unidade': 'un',
            'preco_unitario_reais': '5.00',
            'data_compra': date.today()
        }
        
        form = CompraIngredienteForm(data=form_data, pizzaria=self.pizzaria)
        self.assertTrue(form.is_valid())

    def test_compra_ingrediente_form_peso_valid(self):
        """Testa formulário de compra com peso válido."""
        form_data = {
            'ingrediente': self.ingrediente.id,
            'fornecedor': self.fornecedor.id,
            'quantidade': '5.0',
            'unidade': 'kg',
            'valor_total_reais': '100.00',
            'data_compra': date.today()
        }
        
        form = CompraIngredienteForm(data=form_data, pizzaria=self.pizzaria)
        self.assertTrue(form.is_valid())

    def test_compra_ingrediente_form_unidade_invalid(self):
        """Testa formulário de compra com unidade inválido."""
        form_data = {
            'ingrediente': self.ingrediente.id,
            'fornecedor': self.fornecedor.id,
            'quantidade': '10.5',  # Deve ser inteiro para unidades
            'unidade': 'un',
            'preco_unitario_reais': '5.00',
            'data_compra': date.today()
        }
        
        form = CompraIngredienteForm(data=form_data, pizzaria=self.pizzaria)
        self.assertFalse(form.is_valid())
        self.assertIn('quantidade', form.errors)

    def test_compra_ingrediente_form_missing_price(self):
        """Testa formulário de compra sem preço obrigatório."""
        form_data = {
            'ingrediente': self.ingrediente.id,
            'fornecedor': self.fornecedor.id,
            'quantidade': '10',
            'unidade': 'un',
            'data_compra': date.today()
            # Sem preço unitário
        }
        
        form = CompraIngredienteForm(data=form_data, pizzaria=self.pizzaria)
        self.assertFalse(form.is_valid())
        self.assertIn('preco_unitario_reais', form.errors)


class EstoqueViewsTestCase(TestCase):
    """Testes para as views do módulo estoque."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = Client()
        self.factory = RequestFactory()
        
        # Criar pizzaria
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            endereco="Rua Teste, 123"
        )
        
        # Criar usuário
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        # Criar usuário da pizzaria
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel="dono_pizzaria"
        )
        
        # Criar ingrediente
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo",
            pizzaria=self.pizzaria
        )
        
        # Criar estoque
        self.estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('10.0'),
            preco_compra_atual_centavos=2500
        )
        
        # Criar fornecedor
        self.fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor Teste"
        )

    def test_dashboard_estoque_authenticated(self):
        """Testa acesso ao dashboard com usuário autenticado."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:dashboard_estoque'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard do Estoque')
        self.assertIn('total_ingredientes', response.context)

    def test_dashboard_estoque_unauthenticated(self):
        """Testa acesso ao dashboard sem autenticação."""
        response = self.client.get(reverse('estoque:dashboard_estoque'))
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)

    def test_lista_estoque_authenticated(self):
        """Testa acesso à lista de estoque com usuário autenticado."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:lista_estoque'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Estoque')
        self.assertIn('estoques', response.context)

    def test_lista_estoque_with_filters(self):
        """Testa lista de estoque com filtros."""
        self.client.force_login(self.user)
        
        # Teste com busca
        response = self.client.get(
            reverse('estoque:lista_estoque'), 
            {'busca': 'Queijo'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('estoques', response.context)
        
        # Teste com filtro de estoque baixo
        response = self.client.get(
            reverse('estoque:lista_estoque'), 
            {'filtro_estoque': 'baixo'}
        )
        self.assertEqual(response.status_code, 200)

    def test_editar_estoque_authenticated(self):
        """Testa edição de estoque com usuário autenticado."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('estoque:editar_estoque', args=[self.estoque.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Estoque')

    def test_editar_estoque_post_valid(self):
        """Testa POST válido para edição de estoque."""
        self.client.force_login(self.user)
        
        form_data = {
            'quantidade_atual': '15.0',
            'estoque_minimo': '5.0',
            'estoque_maximo': '25.0',
            'unidade_medida': 'kg',
            'preco_compra_reais': '30.00'
        }
        
        response = self.client.post(
            reverse('estoque:editar_estoque', args=[self.estoque.id]),
            form_data
        )
        
        # Deve redirecionar após sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se o estoque foi atualizado
        self.estoque.refresh_from_db()
        self.assertEqual(self.estoque.quantidade_atual, Decimal('15.0'))
        self.assertEqual(self.estoque.preco_compra_atual_centavos, 3000)

    def test_lista_fornecedores_authenticated(self):
        """Testa acesso à lista de fornecedores."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:lista_fornecedores'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fornecedores')

    def test_adicionar_fornecedor_authenticated(self):
        """Testa adição de fornecedor."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:adicionar_fornecedor'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adicionar Fornecedor')

    def test_adicionar_fornecedor_post_valid(self):
        """Testa POST válido para adição de fornecedor."""
        self.client.force_login(self.user)
        
        form_data = {
            'nome': 'Novo Fornecedor',
            'cnpj': '11.111.111/0001-11',
            'telefone': '(11) 99999-9999',
            'email': 'teste@fornecedor.com',
            'ativo': True
        }
        
        response = self.client.post(
            reverse('estoque:adicionar_fornecedor'),
            form_data
        )
        
        # Deve redirecionar após sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se o fornecedor foi criado
        fornecedor = Fornecedor.objects.filter(nome='Novo Fornecedor').first()
        self.assertIsNotNone(fornecedor)
        self.assertEqual(fornecedor.pizzaria, self.pizzaria)

    def test_lista_compras_authenticated(self):
        """Testa acesso à lista de compras."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:lista_compras'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Histórico de Compras')

    def test_registrar_compra_authenticated(self):
        """Testa acesso ao formulário de registro de compra."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:registrar_compra'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registrar Compra')

    def test_registrar_compra_post_valid(self):
        """Testa POST válido para registro de compra."""
        self.client.force_login(self.user)
        
        form_data = {
            'ingrediente': self.ingrediente.id,
            'fornecedor': self.fornecedor.id,
            'quantidade': '5.0',
            'unidade': 'kg',
            'valor_total_reais': '100.00',
            'data_compra': date.today()
        }
        
        response = self.client.post(
            reverse('estoque:registrar_compra'),
            form_data
        )
        
        # Deve redirecionar após sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se a compra foi criada
        compra = CompraIngrediente.objects.filter(
            ingrediente=self.ingrediente,
            quantidade=Decimal('5.0')
        ).first()
        self.assertIsNotNone(compra)

    def test_historico_precos_authenticated(self):
        """Testa acesso ao histórico de preços."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('estoque:historico_precos', args=[self.ingrediente.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Histórico de Preços')

    def test_relatorio_custos_authenticated(self):
        """Testa acesso ao relatório de custos."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('estoque:relatorio_custos'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Relatório de Custos')

    def test_ajax_ingrediente_preco(self):
        """Testa endpoint AJAX para preço do ingrediente."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('estoque:ajax_ingrediente_preco', args=[self.ingrediente.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['preco_centavos'], 2500)
        self.assertEqual(data['preco_reais'], 25.0)

    def test_super_admin_acesso_estoque_qualquer_pizzaria(self):
        """Testa se super_admin pode acessar estoque de qualquer pizzaria."""
        # Criar super admin
        super_admin_user = get_user_model().objects.create_user(
            username="superadmin",
            password="superpass123"
        )
        
        super_admin_profile = UsuarioPizzaria.objects.create(
            usuario=super_admin_user,
            pizzaria=None,  # Super admin não tem pizzaria específica
            papel="super_admin"
        )
        
        # Criar segunda pizzaria
        segunda_pizzaria = Pizzaria.objects.create(
            nome="Segunda Pizzaria",
            cnpj="98765432109876",
            telefone="(11) 88888-8888"
        )
        
        # Criar ingrediente na segunda pizzaria
        ingrediente_segunda = Ingrediente.objects.create(
            nome="Ingrediente Segunda Pizzaria",
            descricao="Ingrediente da segunda pizzaria",
            pizzaria=segunda_pizzaria
        )
        
        # Criar estoque na segunda pizzaria
        estoque_segunda = EstoqueIngrediente.objects.create(
            ingrediente=ingrediente_segunda,
            quantidade_atual=Decimal('5.0'),
            estoque_minimo=Decimal('1.0'),
            preco_compra_atual_centavos=2000
        )
        
        # Fazer login como super admin
        self.client.login(username='superadmin', password='superpass123')
        
        # Testar acesso ao estoque da segunda pizzaria
        response = self.client.get(
            reverse('estoque:lista_estoque_pizzaria', kwargs={'pizzaria_id': segunda_pizzaria.id})
        )
        
        # Deve retornar 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Deve conter o estoque da segunda pizzaria
        self.assertContains(response, "Ingrediente Segunda Pizzaria")
        self.assertContains(response, "5.0")
        
        # Deve mostrar que é super admin
        self.assertContains(response, "Segunda Pizzaria")
        
        # Verificar se o contexto contém as informações corretas
        self.assertEqual(response.context['pizzaria_atual'], segunda_pizzaria)
        self.assertTrue(response.context['is_super_admin'])
        
        # Testar que super admin não pode acessar estoque de pizzaria inexistente
        response_invalida = self.client.get(
            reverse('estoque:lista_estoque_pizzaria', kwargs={'pizzaria_id': 99999})
        )
        
        # Deve redirecionar para lista de estoque com mensagem de erro
        self.assertEqual(response_invalida.status_code, 302)
        
    def test_super_admin_acesso_estoque_propria_pizzaria(self):
        """Testa se super_admin pode acessar estoque de sua própria pizzaria (se tiver uma)."""
        # Criar super admin com pizzaria
        super_admin_user = get_user_model().objects.create_user(
            username="superadmin_com_pizzaria",
            password="superpass123"
        )
        
        super_admin_profile = UsuarioPizzaria.objects.create(
            usuario=super_admin_user,
            pizzaria=self.pizzaria,  # Super admin com pizzaria
            papel="super_admin"
        )
        
        # Fazer login como super admin
        self.client.login(username='superadmin_com_pizzaria', password='superpass123')
        
        # Testar acesso ao estoque da própria pizzaria
        response = self.client.get(reverse('estoque:lista_estoque'))
        
        # Deve retornar 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Deve conter o estoque da própria pizzaria (verificar nome correto)
        self.assertContains(response, "Queijo")
        
        # Deve mostrar que é super admin
        self.assertTrue(response.context['is_super_admin'])
        
        # Deve usar a pizzaria correta
        self.assertEqual(response.context['pizzaria_atual'], self.pizzaria)

    def test_usuario_normal_nao_pode_acessar_estoque_outra_pizzaria(self):
        """Testa se usuário normal não pode acessar estoque de outra pizzaria."""
        # Criar segunda pizzaria
        segunda_pizzaria = Pizzaria.objects.create(
            nome="Segunda Pizzaria",
            cnpj="98765432109876",
            telefone="(11) 88888-8888"
        )
        
        # Criar usuário normal da segunda pizzaria
        usuario_normal = get_user_model().objects.create_user(
            username="usuario_normal",
            password="normalpass123"
        )
        
        usuario_normal_profile = UsuarioPizzaria.objects.create(
            usuario=usuario_normal,
            pizzaria=segunda_pizzaria,
            papel="dono_pizzaria"
        )
        
        # Fazer login como usuário normal
        self.client.login(username='usuario_normal', password='normalpass123')
        
        # Tentar acessar estoque da primeira pizzaria (deve falhar)
        response = self.client.get(
            reverse('estoque:lista_estoque_pizzaria', kwargs={'pizzaria_id': self.pizzaria.id})
        )
        
        # Deve redirecionar para lista de estoque (acesso negado)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que foi redirecionado para a lista de estoque da própria pizzaria
        self.assertIn('/estoque/estoque/', response.url)
        
        # Verificar que não é super admin
        response_propria = self.client.get(reverse('estoque:lista_estoque'))
        self.assertFalse(response_propria.context['is_super_admin'])


class EstoqueIntegrationTestCase(TestCase):
    """Testes de integração para o módulo estoque."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = Client()
        
        # Criar pizzaria
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            endereco="Rua Teste, 123"
        )
        
        # Criar usuário
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        # Criar usuário da pizzaria
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel="dono_pizzaria"
        )
        
        # Criar ingredientes
        self.queijo = Ingrediente.objects.create(
            nome="Queijo Mussarela",
            pizzaria=self.pizzaria
        )
        
        self.tomate = Ingrediente.objects.create(
            nome="Tomate",
            pizzaria=self.pizzaria
        )
        
        # Criar fornecedor
        self.fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor Teste"
        )

    def test_fluxo_completo_estoque(self):
        """Testa fluxo completo de gestão de estoque."""
        self.client.force_login(self.user)
        
        # 1. Acessar dashboard
        response = self.client.get(reverse('estoque:dashboard_estoque'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Adicionar fornecedor
        form_data = {
            'nome': 'Novo Fornecedor',
            'cnpj': '11.111.111/0001-11',
            'telefone': '(11) 99999-9999',
            'email': 'teste@fornecedor.com',
            'ativo': True
        }
        
        response = self.client.post(
            reverse('estoque:adicionar_fornecedor'),
            form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 3. Registrar compra
        form_data = {
            'ingrediente': self.queijo.id,
            'fornecedor': self.fornecedor.id,
            'quantidade': '10.0',
            'unidade': 'kg',
            'valor_total_reais': '200.00',
            'data_compra': date.today()
        }
        
        response = self.client.post(
            reverse('estoque:registrar_compra'),
            form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar se estoque foi criado/atualizado
        estoque = EstoqueIngrediente.objects.filter(
            ingrediente=self.queijo
        ).first()
        self.assertIsNotNone(estoque)
        self.assertEqual(estoque.quantidade_atual, Decimal('10.0'))
        
        # 5. Verificar se compra foi registrada
        compra = CompraIngrediente.objects.filter(
            ingrediente=self.queijo
        ).first()
        self.assertIsNotNone(compra)
        self.assertEqual(compra.valor_total_centavos, 20000)
        
        # 6. Verificar se histórico foi criado
        historico = HistoricoPrecoCompra.objects.filter(
            ingrediente=self.queijo
        ).first()
        self.assertIsNotNone(historico)

    def test_gestao_estoque_multiplos_ingredientes(self):
        """Testa gestão de estoque com múltiplos ingredientes."""
        self.client.force_login(self.user)
        
        # Registrar compras para diferentes ingredientes
        compras_data = [
            {
                'ingrediente': self.queijo.id,
                'quantidade': '5.0',
                'unidade': 'kg',
                'valor_total_reais': '100.00'
            },
            {
                'ingrediente': self.tomate.id,
                'quantidade': '3.0',
                'unidade': 'kg',
                'valor_total_reais': '30.00'
            }
        ]
        
        for compra_data in compras_data:
            compra_data['fornecedor'] = self.fornecedor.id
            compra_data['data_compra'] = date.today()
            
            response = self.client.post(
                reverse('estoque:registrar_compra'),
                compra_data
            )
            self.assertEqual(response.status_code, 302)
        
        # Verificar se todos os estoques foram criados
        estoques = EstoqueIngrediente.objects.filter(
            ingrediente__pizzaria=self.pizzaria
        )
        self.assertEqual(estoques.count(), 2)
        
        # Verificar se todas as compras foram registradas
        compras = CompraIngrediente.objects.filter(
            ingrediente__pizzaria=self.pizzaria
        )
        self.assertEqual(compras.count(), 2)

    def test_edicao_estoque_existente(self):
        """Testa edição de estoque existente."""
        self.client.force_login(self.user)
        
        # Criar estoque inicial
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.queijo,
            quantidade_atual=Decimal('5.0'),
            estoque_minimo=Decimal('1.0'),
            preco_compra_atual_centavos=2000
        )
        
        # Editar estoque
        form_data = {
            'quantidade_atual': '8.0',
            'estoque_minimo': '2.0',
            'estoque_maximo': '15.0',
            'unidade_medida': 'kg',
            'preco_compra_reais': '25.00'
        }
        
        response = self.client.post(
            reverse('estoque:editar_estoque', args=[estoque.id]),
            form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verificar alterações
        estoque.refresh_from_db()
        self.assertEqual(estoque.quantidade_atual, Decimal('8.0'))
        self.assertEqual(estoque.estoque_minimo, Decimal('2.0'))
        self.assertEqual(estoque.preco_compra_atual_centavos, 2500)

    def test_filtros_lista_estoque(self):
        """Testa filtros da lista de estoque."""
        self.client.force_login(self.user)
        
        # Criar estoques com diferentes quantidades
        EstoqueIngrediente.objects.create(
            ingrediente=self.queijo,
            quantidade_atual=Decimal('0.0'),  # Estoque zerado
            estoque_minimo=Decimal('1.0'),
            preco_compra_atual_centavos=2000
        )
        
        EstoqueIngrediente.objects.create(
            ingrediente=self.tomate,
            quantidade_atual=Decimal('0.5'),  # Estoque baixo
            estoque_minimo=Decimal('1.0'),
            preco_compra_atual_centavos=1500
        )
        
        # Teste filtro estoque baixo
        response = self.client.get(
            reverse('estoque:lista_estoque'),
            {'filtro_estoque': 'baixo'}
        )
        self.assertEqual(response.status_code, 200)
        
        # Teste filtro estoque zerado
        response = self.client.get(
            reverse('estoque:lista_estoque'),
            {'filtro_estoque': 'zerado'}
        )
        self.assertEqual(response.status_code, 200)
        
        # Teste busca por nome
        response = self.client.get(
            reverse('estoque:lista_estoque'),
            {'busca': 'Queijo'}
        )
        self.assertEqual(response.status_code, 200)

    def test_gestao_fornecedores(self):
        """Testa gestão completa de fornecedores."""
        self.client.force_login(self.user)
        
        # Adicionar fornecedor
        form_data = {
            'nome': 'Fornecedor A',
            'cnpj': '11.111.111/0001-11',
            'telefone': '(11) 11111-1111',
            'email': 'a@fornecedor.com',
            'ativo': True
        }
        
        response = self.client.post(
            reverse('estoque:adicionar_fornecedor'),
            form_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Buscar fornecedor criado
        fornecedor = Fornecedor.objects.filter(nome='Fornecedor A').first()
        self.assertIsNotNone(fornecedor)
        
        # Editar fornecedor
        form_data_edit = {
            'nome': 'Fornecedor A Editado',
            'cnpj': '11.111.111/0001-11',
            'telefone': '(11) 11111-1111',
            'email': 'a@fornecedor.com',
            'ativo': False
        }
        
        response = self.client.post(
            reverse('estoque:editar_fornecedor', args=[fornecedor.id]),
            form_data_edit
        )
        self.assertEqual(response.status_code, 302)
        
        # Verificar alterações
        fornecedor.refresh_from_db()
        self.assertEqual(fornecedor.nome, 'Fornecedor A Editado')
        self.assertFalse(fornecedor.ativo)


class EstoqueAPITestCase(TestCase):
    """Testes para APIs do módulo estoque."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = Client()
        
        # Criar pizzaria
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            endereco="Rua Teste, 123"
        )
        
        # Criar usuário
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        # Criar usuário da pizzaria
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel="dono_pizzaria"
        )
        
        # Criar ingrediente
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo",
            pizzaria=self.pizzaria
        )
        
        # Criar estoque
        self.estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('10.0'),
            preco_compra_atual_centavos=2500
        )

    def test_ajax_ingrediente_preco_success(self):
        """Testa endpoint AJAX com ingrediente válido."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('estoque:ajax_ingrediente_preco', args=[self.ingrediente.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['preco_centavos'], 2500)
        self.assertEqual(data['preco_reais'], 25.0)

    def test_ajax_ingrediente_preco_invalid_id(self):
        """Testa endpoint AJAX com ID inválido."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('estoque:ajax_ingrediente_preco', args=[99999])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertEqual(data['preco_centavos'], 0)
        self.assertEqual(data['preco_reais'], 0)

    def test_ajax_ingrediente_preco_unauthenticated(self):
        """Testa endpoint AJAX sem autenticação."""
        response = self.client.get(
            reverse('estoque:ajax_ingrediente_preco', args=[self.ingrediente.id])
        )
        
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)


class EstoqueEdgeCasesTestCase(TestCase):
    """Testes para casos extremos e edge cases do módulo estoque."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste",
            cnpj="12345678000190",
            endereco="Rua Teste, 123"
        )
        
        self.ingrediente = Ingrediente.objects.create(
            nome="Ingrediente Teste",
            pizzaria=self.pizzaria
        )

    def test_estoque_quantidade_zero(self):
        """Testa estoque com quantidade zero."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('0.0'),
            estoque_minimo=Decimal('1.0'),
            preco_compra_atual_centavos=1000
        )
        
        self.assertEqual(estoque.valor_total_estoque, Decimal('0.00'))
        self.assertTrue(estoque.estoque_baixo)

    def test_estoque_preco_zero(self):
        """Testa estoque com preço zero."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('10.0'),
            preco_compra_atual_centavos=0
        )
        
        self.assertEqual(estoque.preco_compra_atual, Decimal('0.00'))
        self.assertEqual(estoque.valor_total_estoque, Decimal('0.00'))

    def test_compra_quantidade_muito_pequena(self):
        """Testa compra com quantidade muito pequena."""
        fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor Teste"
        )
        
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            fornecedor=fornecedor,
            quantidade=Decimal('0.001'),  # 1 grama
            unidade='kg',
            preco_unitario_centavos=1000,
            data_compra=date.today()
        )
        
        self.assertEqual(compra.valor_total_centavos, 1)  # 0.001 * 1000 = 1 centavo

    def test_estoque_unidades_diferentes(self):
        """Testa estoque com unidades de medida diferentes."""
        # Criar estoque em kg
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('1.0'),
            unidade_medida='kg',
            preco_compra_atual_centavos=1000  # R$ 10,00/kg
        )
        
        # Registrar compra em gramas
        fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor Teste"
        )
        
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            fornecedor=fornecedor,
            quantidade=Decimal('500.0'),  # 500g
            unidade='g',
            preco_unitario_centavos=10,  # R$ 0,10/g
            data_compra=date.today()
        )
        
        # Verificar se o estoque foi atualizado corretamente
        estoque.refresh_from_db()
        # O sistema converte automaticamente unidades diferentes
        # 500g = 0.5kg, então 1kg + 0.5kg = 1.5kg
        self.assertEqual(estoque.quantidade_atual, Decimal('1.5'))  # 1kg + 0.5kg
        # Preço convertido: R$ 0,10/g = R$ 100,00/kg
        self.assertEqual(estoque.preco_compra_atual_centavos, 10000)  # R$ 100,00/kg

    def test_estoque_estoque_minimo_maximo_iguais(self):
        """Testa estoque com mínimo e máximo iguais."""
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('5.0'),
            estoque_minimo=Decimal('5.0'),
            estoque_maximo=Decimal('5.0'),
            preco_compra_atual_centavos=1000
        )
        
        # Estoque está exatamente no mínimo
        self.assertTrue(estoque.estoque_baixo)

    def test_compra_sem_fornecedor(self):
        """Testa compra sem fornecedor."""
        compra = CompraIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade=Decimal('2.0'),
            unidade='kg',
            preco_unitario_centavos=1500,
            data_compra=date.today()
        )
        
        self.assertIsNone(compra.fornecedor)
        self.assertEqual(compra.quantidade, Decimal('2.0'))

    def test_historico_preco_sem_compra(self):
        """Testa histórico de preço sem compra associada."""
        historico = HistoricoPrecoCompra.objects.create(
            ingrediente=self.ingrediente,
            preco_centavos=2000,
            data_preco=date.today(),
            fornecedor="Fornecedor Teste"
        )
        
        self.assertIsNone(historico.compra)
        self.assertEqual(historico.preco_centavos, 2000)
