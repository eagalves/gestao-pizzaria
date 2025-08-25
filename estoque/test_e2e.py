from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date
import time

from autenticacao.models import Pizzaria, UsuarioPizzaria
from ingredientes.models import Ingrediente
from .models import Fornecedor, EstoqueIngrediente, CompraIngrediente


class EstoqueE2ETestCase(LiveServerTestCase):
    """Testes end-to-end para o módulo estoque usando Selenium."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        super().setUpClass()
        
        # Verificar se o Selenium está disponível
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            
            cls.webdriver = webdriver
            cls.By = By
            cls.WebDriverWait = WebDriverWait
            cls.EC = EC
            cls.Options = Options
            
            # Configurar Chrome em modo headless
            chrome_options = cls.Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            cls.driver = cls.webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
            
        except ImportError:
            # Selenium não disponível, pular testes
            cls.driver = None
            print("Selenium não disponível. Testes E2E serão pulados.")
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes."""
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        super().setUp()
        
        # Verificar se o Selenium está disponível
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Tentar configurar o driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            self.driver.implicitly_wait(10)
        except Exception as e:
            self.driver = None
            print(f"Selenium não disponível: {e}")
        
        if not self.driver:
            self.skipTest("Selenium não disponível - pulando teste E2E")
        
        # Criar dados de teste
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Teste E2E",
            cnpj="12345678000190",
            telefone="(11) 99999-9999"
        )
        
        self.user = get_user_model().objects.create_user(
            username="testuser_e2e",
            email="teste@teste.com",
            password="testpass123"
        )
        
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel="dono_pizzaria"
        )
        
        self.ingrediente = Ingrediente.objects.create(
            nome="Queijo Mussarela E2E",
            descricao="Queijo mussarela para testes E2E",
            pizzaria=self.pizzaria
        )
        
        self.fornecedor = Fornecedor.objects.create(
            pizzaria=self.pizzaria,
            nome="Fornecedor E2E",
            cnpj="98765432000110",
            telefone="(11) 88888-8888",
            email="fornecedor@teste.com",
            ativo=True
        )
    
    def tearDown(self):
        """Limpeza após cada teste."""
        # Limpar cookies e sessão
        if self.driver:
            self.driver.delete_all_cookies()
        super().tearDown()
    
    def login_user(self):
        """Faz login do usuário."""
        # Ir para página de login
        self.driver.get(f"{self.live_server_url}/autenticacao/login/")
        
        # Preencher formulário de login
        username_input = self.driver.find_element(self.By.NAME, "username")
        password_input = self.driver.find_element(self.By.NAME, "password")
        
        username_input.send_keys("testuser_e2e")
        password_input.send_keys("testpass123")
        
        # Submeter formulário
        submit_button = self.driver.find_element(self.By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar redirecionamento
        time.sleep(2)
    
    def test_dashboard_estoque_e2e(self):
        """Testa acesso ao dashboard do estoque via interface."""
        self.login_user()
        
        # Ir para dashboard do estoque
        self.driver.get(f"{self.live_server_url}/estoque/")
        
        # Verificar se a página carregou
        self.assertIn("Dashboard", self.driver.title)
        
        # Verificar elementos da página
        self.assertTrue(
            self.driver.find_element(self.By.CSS_SELECTOR, "h1").text.lower().find("estoque") != -1
        )
    
    def test_lista_estoque_e2e(self):
        """Testa lista de estoque via interface."""
        self.login_user()
        
        # Ir para lista de estoque
        self.driver.get(f"{self.live_server_url}/estoque/estoque/")
        
        # Verificar se a página carregou
        self.assertIn("Estoque", self.driver.title)
        
        # Verificar se há elementos de filtro
        busca_input = self.driver.find_element(self.By.NAME, "busca")
        self.assertIsNotNone(busca_input)
        
        filtro_select = self.driver.find_element(self.By.NAME, "filtro_estoque")
        self.assertIsNotNone(filtro_select)
    
    def test_adicionar_fornecedor_e2e(self):
        """Testa adição de fornecedor via interface."""
        self.login_user()
        
        # Ir para página de adicionar fornecedor
        self.driver.get(f"{self.live_server_url}/estoque/fornecedores/adicionar/")
        
        # Verificar se a página carregou
        self.assertIn("Fornecedor", self.driver.title)
        
        # Preencher formulário
        nome_input = self.driver.find_element(self.By.NAME, "nome")
        cnpj_input = self.driver.find_element(self.By.NAME, "cnpj")
        telefone_input = self.driver.find_element(self.By.NAME, "telefone")
        email_input = self.driver.find_element(self.By.NAME, "email")
        
        nome_input.send_keys("Fornecedor E2E Teste")
        cnpj_input.send_keys("11.111.111/0001-11")
        telefone_input.send_keys("(11) 77777-7777")
        email_input.send_keys("e2e@fornecedor.com")
        
        # Submeter formulário
        submit_button = self.driver.find_element(self.By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar redirecionamento
        time.sleep(2)
        
        # Verificar se foi redirecionado para lista de fornecedores
        self.assertIn("fornecedores", self.driver.current_url)
        
        # Verificar se o fornecedor foi criado no banco
        fornecedor = Fornecedor.objects.filter(nome="Fornecedor E2E Teste").first()
        self.assertIsNotNone(fornecedor)
    
    def test_registrar_compra_e2e(self):
        """Testa registro de compra via interface."""
        self.login_user()
        
        # Ir para página de registrar compra
        self.driver.get(f"{self.live_server_url}/estoque/compras/registrar/")
        
        # Verificar se a página carregou
        self.assertIn("Compra", self.driver.title)
        
        # Preencher formulário
        ingrediente_select = self.driver.find_element(self.By.NAME, "ingrediente")
        fornecedor_select = self.driver.find_element(self.By.NAME, "fornecedor")
        quantidade_input = self.driver.find_element(self.By.NAME, "quantidade")
        unidade_select = self.driver.find_element(self.By.NAME, "unidade")
        valor_total_input = self.driver.find_element(self.By.NAME, "valor_total_reais")
        
        # Selecionar ingrediente
        from selenium.webdriver.support.ui import Select
        ingrediente_dropdown = Select(ingrediente_select)
        ingrediente_dropdown.select_by_visible_text("Queijo Mussarela E2E")
        
        # Selecionar fornecedor
        fornecedor_dropdown = Select(fornecedor_select)
        fornecedor_dropdown.select_by_visible_text("Fornecedor E2E")
        
        # Preencher quantidade e valor
        quantidade_input.send_keys("5.0")
        unidade_dropdown = Select(unidade_select)
        unidade_dropdown.select_by_visible_text("Quilos (kg)")
        valor_total_input.send_keys("100.00")
        
        # Submeter formulário
        submit_button = self.driver.find_element(self.By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar redirecionamento
        time.sleep(2)
        
        # Verificar se foi redirecionado para lista de compras
        self.assertIn("compras", self.driver.current_url)
        
        # Verificar se a compra foi criada no banco
        compra = CompraIngrediente.objects.filter(
            ingrediente=self.ingrediente,
            quantidade=Decimal('5.0')
        ).first()
        self.assertIsNotNone(compra)
        self.assertEqual(compra.valor_total_centavos, 10000)  # R$ 100,00
    
    def test_editar_estoque_e2e(self):
        """Testa edição de estoque via interface."""
        # Criar estoque para editar
        estoque = EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('10.0'),
            estoque_minimo=Decimal('2.0'),
            preco_compra_atual_centavos=2500
        )
        
        self.login_user()
        
        # Ir para página de editar estoque
        self.driver.get(f"{self.live_server_url}/estoque/estoque/{estoque.id}/editar/")
        
        # Verificar se a página carregou
        self.assertIn("Editar", self.driver.title)
        
        # Preencher formulário
        quantidade_input = self.driver.find_element(self.By.NAME, "quantidade_atual")
        estoque_minimo_input = self.driver.find_element(self.By.NAME, "estoque_minimo")
        preco_input = self.driver.find_element(self.By.NAME, "preco_compra_reais")
        
        # Limpar campos e preencher novos valores
        quantidade_input.clear()
        estoque_minimo_input.clear()
        preco_input.clear()
        
        quantidade_input.send_keys("15.0")
        estoque_minimo_input.send_keys("5.0")
        preco_input.send_keys("30.00")
        
        # Submeter formulário
        submit_button = self.driver.find_element(self.By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar redirecionamento
        time.sleep(2)
        
        # Verificar se foi redirecionado para lista de estoque
        self.assertIn("estoque", self.driver.current_url)
        
        # Verificar se o estoque foi atualizado no banco
        estoque.refresh_from_db()
        self.assertEqual(estoque.quantidade_atual, Decimal('15.0'))
        self.assertEqual(estoque.estoque_minimo, Decimal('5.0'))
        self.assertEqual(estoque.preco_compra_atual_centavos, 3000)
    
    def test_filtros_lista_estoque_e2e(self):
        """Testa filtros da lista de estoque via interface."""
        # Criar estoques com diferentes quantidades
        EstoqueIngrediente.objects.create(
            ingrediente=self.ingrediente,
            quantidade_atual=Decimal('0.5'),  # Estoque baixo
            estoque_minimo=Decimal('1.0'),
            preco_compra_atual_centavos=2000
        )
        
        self.login_user()
        
        # Ir para lista de estoque
        self.driver.get(f"{self.live_server_url}/estoque/estoque/")
        
        # Testar filtro de estoque baixo
        filtro_select = self.driver.find_element(self.By.NAME, "filtro_estoque")
        filtro_dropdown = Select(filtro_select)
        filtro_dropdown.select_by_visible_text("Estoque baixo")
        
        # Aplicar filtro
        filtro_form = self.driver.find_element(self.By.CSS_SELECTOR, "form")
        filtro_form.submit()
        
        # Aguardar carregamento
        time.sleep(1)
        
        # Verificar se o filtro foi aplicado
        self.assertIn("filtro_estoque=baixo", self.driver.current_url)
        
        # Testar busca por nome
        busca_input = self.driver.find_element(self.By.NAME, "busca")
        busca_input.clear()
        busca_input.send_keys("Queijo")
        
        # Aplicar busca
        busca_form = self.driver.find_element(self.By.CSS_SELECTOR, "form")
        busca_form.submit()
        
        # Aguardar carregamento
        time.sleep(1)
        
        # Verificar se a busca foi aplicada
        self.assertIn("busca=Queijo", self.driver.current_url)
    
    def test_navegacao_menu_e2e(self):
        """Testa navegação entre diferentes seções do estoque."""
        self.login_user()
        
        # Ir para dashboard
        self.driver.get(f"{self.live_server_url}/estoque/")
        
        # Verificar se há links de navegação
        estoque_link = self.driver.find_element(self.By.CSS_SELECTOR, "a[href*='estoque/']")
        fornecedores_link = self.driver.find_element(self.By.CSS_SELECTOR, "a[href*='fornecedores/']")
        compras_link = self.driver.find_element(self.By.CSS_SELECTOR, "a[href*='compras/']")
        
        self.assertIsNotNone(estoque_link)
        self.assertIsNotNone(fornecedores_link)
        self.assertIsNotNone(compras_link)
        
        # Testar navegação para lista de fornecedores
        fornecedores_link.click()
        time.sleep(1)
        
        self.assertIn("fornecedores", self.driver.current_url)
        
        # Testar navegação para lista de compras
        compras_link = self.driver.find_element(self.By.CSS_SELECTOR, "a[href*='compras/']")
        compras_link.click()
        time.sleep(1)
        
        self.assertIn("compras", self.driver.current_url)
    
    def test_responsividade_interface_e2e(self):
        """Testa responsividade da interface em diferentes tamanhos de tela."""
        self.login_user()
        
        # Ir para dashboard
        self.driver.get(f"{self.live_server_url}/estoque/")
        
        # Testar diferentes resoluções
        resolutions = [
            (1920, 1080),  # Desktop
            (1366, 768),   # Laptop
            (768, 1024),   # Tablet
            (375, 667),    # Mobile
        ]
        
        for width, height in resolutions:
            self.driver.set_window_size(width, height)
            time.sleep(1)
            
            # Verificar se a página ainda carrega corretamente
            self.assertIn("Dashboard", self.driver.title)
            
            # Verificar se elementos principais estão visíveis
            main_content = self.driver.find_element(self.By.CSS_SELECTOR, "main, .container, .content")
            self.assertTrue(main_content.is_displayed())
    
    def test_erros_formulario_e2e(self):
        """Testa tratamento de erros nos formulários."""
        self.login_user()
        
        # Ir para página de adicionar fornecedor
        self.driver.get(f"{self.live_server_url}/estoque/fornecedores/adicionar/")
        
        # Tentar submeter formulário vazio
        submit_button = self.driver.find_element(self.By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Aguardar validação
        time.sleep(1)
        
        # Verificar se há mensagens de erro
        error_messages = self.driver.find_elements(self.By.CSS_SELECTOR, ".error, .alert-danger, .invalid-feedback")
        
        # Deve haver pelo menos uma mensagem de erro (nome obrigatório)
        self.assertGreater(len(error_messages), 0)
        
        # Verificar se o formulário não foi submetido (deve estar na mesma página)
        self.assertIn("adicionar", self.driver.current_url)
    
    def test_autenticacao_seguranca_e2e(self):
        """Testa segurança e autenticação."""
        # Tentar acessar dashboard sem login
        self.driver.get(f"{self.live_server_url}/estoque/")
        
        # Deve ser redirecionado para login
        self.assertIn("login", self.driver.current_url)
        
        # Tentar acessar outras páginas sem login
        self.driver.get(f"{self.live_server_url}/estoque/estoque/")
        self.assertIn("login", self.driver.current_url)
        
        self.driver.get(f"{self.live_server_url}/estoque/fornecedores/")
        self.assertIn("login", self.driver.current_url)
        
        # Fazer login
        self.login_user()
        
        # Agora deve conseguir acessar as páginas
        self.driver.get(f"{self.live_server_url}/estoque/")
        self.assertIn("estoque", self.driver.current_url)
        
        # Tentar acessar estoque de outra pizzaria (deve falhar)
        outra_pizzaria = Pizzaria.objects.create(
            nome="Outra Pizzaria",
            cnpj="00.000.000/0000-00"
        )
        
        outro_ingrediente = Ingrediente.objects.create(
            nome="Outro Ingrediente",
            pizzaria=outra_pizzaria
        )
        
        outro_estoque = EstoqueIngrediente.objects.create(
            ingrediente=outro_ingrediente,
            quantidade_atual=Decimal('10.0'),
            preco_compra_atual_centavos=1000
        )
        
        # Tentar editar estoque de outra pizzaria
        self.driver.get(f"{self.live_server_url}/estoque/estoque/{outro_estoque.id}/editar/")
        
        # Deve receber erro 404 ou ser redirecionado
        self.assertNotIn("editar", self.driver.current_url)


class EstoquePerformanceE2ETestCase(LiveServerTestCase):
    """Testes de performance para o módulo estoque."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        super().setUpClass()
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            cls.webdriver = webdriver
            cls.Options = Options
            
            chrome_options = cls.Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            cls.driver = cls.webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(5)  # Timeout menor para testes de performance
            
        except ImportError:
            cls.driver = None
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes."""
        if cls.driver:
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        super().setUp()
        
        # Verificar se o Selenium está disponível
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Tentar configurar o driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            self.driver.implicitly_wait(10)
        except Exception as e:
            self.driver = None
            print(f"Selenium não disponível: {e}")
        
        if not self.driver:
            self.skipTest("Selenium não disponível - pulando teste E2E de performance")
        
        # Criar dados de teste
        self.pizzaria = Pizzaria.objects.create(
            nome="Pizzaria Performance",
            cnpj="12345678000190"
        )
        
        self.user = get_user_model().objects.create_user(
            username="testuser_perf",
            password="testpass123"
        )
        
        self.usuario_pizzaria = UsuarioPizzaria.objects.create(
            usuario=self.user,
            pizzaria=self.pizzaria,
            papel="dono_pizzaria"
        )
        
        # Criar muitos ingredientes para testar performance
        for i in range(50):
            ingrediente = Ingrediente.objects.create(
                nome=f"Ingrediente {i}",
                pizzaria=self.pizzaria
            )
            
            EstoqueIngrediente.objects.create(
                ingrediente=ingrediente,
                quantidade_atual=Decimal('10.0'),
                preco_compra_atual_centavos=1000
            )
    
    def test_performance_lista_estoque_grande(self):
        """Testa performance da lista de estoque com muitos itens."""
        self.login_user()
        
        start_time = time.time()
        
        # Carregar lista de estoque
        self.driver.get(f"{self.live_server_url}/estoque/estoque/")
        
        load_time = time.time() - start_time
        
        # Verificar se carregou em tempo razoável (menos de 3 segundos)
        self.assertLess(load_time, 3.0)
        
        # Verificar se todos os itens foram carregados
        estoque_items = self.driver.find_elements(self.By.CSS_SELECTOR, "tr, .estoque-item")
        self.assertGreater(len(estoque_items), 50)
    
    def test_performance_busca_estoque(self):
        """Testa performance da busca em estoque."""
        self.login_user()
        
        # Ir para lista de estoque
        self.driver.get(f"{self.live_server_url}/estoque/estoque/")
        
        start_time = time.time()
        
        # Fazer busca
        busca_input = self.driver.find_element(self.By.NAME, "busca")
        busca_input.send_keys("Ingrediente 25")
        
        busca_form = self.driver.find_element(self.By.CSS_SELECTOR, "form")
        busca_form.submit()
        
        search_time = time.time() - start_time
        
        # Verificar se a busca foi rápida (menos de 2 segundos)
        self.assertLess(search_time, 2.0)
        
        # Verificar se o resultado foi correto
        self.assertIn("Ingrediente 25", self.driver.page_source)
    
    def test_performance_dashboard_estoque(self):
        """Testa performance do dashboard com muitos dados."""
        self.login_user()
        
        start_time = time.time()
        
        # Carregar dashboard
        self.driver.get(f"{self.live_server_url}/estoque/")
        
        load_time = time.time() - start_time
        
        # Verificar se carregou em tempo razoável (menos de 2 segundos)
        self.assertLess(load_time, 2.0)
        
        # Verificar se as estatísticas foram calculadas
        self.assertIn("50", self.driver.page_source)  # Total de ingredientes
