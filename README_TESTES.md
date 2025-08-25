# Guia de Testes - Sistema de Gestão de Pizzaria

Este documento descreve como executar e manter os testes do sistema de gestão de pizzaria.

## 📋 Visão Geral

O projeto possui uma cobertura completa de testes incluindo:

- **Testes Unitários**: Testam funcionalidades individuais dos modelos, views e forms
- **Testes de Integração**: Testam a interação entre diferentes componentes
- **Testes End-to-End**: Testam o fluxo completo através da interface do usuário
- **Testes de Performance**: Testam o comportamento sob carga

## 🚀 Instalação das Dependências

### Dependências Básicas
```bash
pip install -r requirements.txt
```

### Dependências de Teste
```bash
pip install -r requirements-test.txt
```

### Dependências Opcionais para E2E
```bash
pip install selenium webdriver-manager
```

## 🧪 Executando os Testes

### 1. Testes Unitários (Django padrão)
```bash
# Todos os testes
python manage.py test

# Testes específicos do módulo estoque
python manage.py test estoque.tests

# Testes com verbosidade
python manage.py test -v 2

# Testes específicos de uma classe
python manage.py test estoque.tests.EstoqueModelsTestCase
```

### 2. Testes com Pytest
```bash
# Todos os testes
pytest

# Testes específicos do módulo
pytest estoque/

# Testes com cobertura
pytest --cov=estoque --cov-report=html

# Testes em paralelo
pytest -n auto
```

### 3. Script de Execução Personalizado
```bash
# Executar todos os testes
python run_tests.py --all

# Apenas testes unitários
python run_tests.py --unit

# Testes com cobertura
python run_tests.py --coverage

# Testes end-to-end
python run_tests.py --e2e

# Testes de um módulo específico
python run_tests.py --module estoque

# Modo verboso
python run_tests.py --unit --verbose
```

## 📊 Cobertura de Código

### Gerar Relatório de Cobertura
```bash
# Executar testes com cobertura
coverage run --source='.' manage.py test

# Relatório no terminal
coverage report

# Relatório HTML (abrir htmlcov/index.html)
coverage html
```

### Configuração de Cobertura
- Arquivo: `.coveragerc`
- Meta de cobertura: 80%
- Relatórios: HTML e terminal
- Exclusões: migrações, arquivos de configuração, etc.

## 🔍 Tipos de Teste

### 1. Testes de Modelos (`EstoqueModelsTestCase`)
- Criação e validação de objetos
- Relacionamentos entre modelos
- Métodos personalizados
- Validações de negócio

### 2. Testes de Formulários (`EstoqueFormsTestCase`)
- Validação de dados
- Limpeza de campos
- Tratamento de erros
- Lógica de negócio nos forms

### 3. Testes de Views (`EstoqueViewsTestCase`)
- Respostas HTTP
- Autenticação e autorização
- Contexto das views
- Redirecionamentos

### 4. Testes de Integração (`EstoqueIntegrationTestCase`)
- Fluxos completos de negócio
- Interação entre modelos
- Cenários reais de uso

### 5. Testes End-to-End (`EstoqueE2ETestCase`)
- Interface do usuário
- Navegação entre páginas
- Preenchimento de formulários
- Validação de resultados

### 6. Testes de Performance (`EstoquePerformanceE2ETestCase`)
- Tempo de carregamento
- Comportamento com muitos dados
- Otimizações de consulta

## 🏭 Factories para Testes

### Uso Básico
```python
from estoque.factories import FornecedorFactory, EstoqueIngredienteFactory

# Criar um fornecedor
fornecedor = FornecedorFactory()

# Criar estoque com ingrediente
estoque = EstoqueIngredienteFactory()
```

### Factories Especializadas
```python
from estoque.factories import EstoqueCompletoFactory, EstoqueBaixoFactory

# Criar conjunto completo de dados
dados = EstoqueCompletoFactory.create_estoque_completo(
    num_ingredientes=10,
    num_fornecedores=5
)

# Criar ingredientes com estoque baixo
estoques_baixos = EstoqueBaixoFactory.create_estoque_baixo(num_ingredientes=3)
```

## 🎯 Marcadores de Teste

### Marcadores Disponíveis
```bash
# Testes lentos
pytest -m "not slow"

# Apenas testes de integração
pytest -m integration

# Testes end-to-end
pytest -m e2e

# Testes de performance
pytest -m performance

# Testes que requerem Selenium
pytest -m selenium
```

## 🐛 Solução de Problemas

### Erro: "Selenium não disponível"
```bash
pip install selenium webdriver-manager
```

### Erro: "ChromeDriver não encontrado"
```bash
# Instalar ChromeDriver automaticamente
pip install webdriver-manager
```

### Erro: "Database não configurada"
```bash
# Verificar configurações do banco
python manage.py check

# Criar banco de teste
python manage.py migrate --run-syncdb
```

### Erro: "Módulo não encontrado"
```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ou usar o script de testes
python run_tests.py --install
```

## 📈 Monitoramento de Qualidade

### Métricas Importantes
- **Cobertura de código**: Mínimo 80%
- **Tempo de execução**: Máximo 5 minutos para todos os testes
- **Taxa de sucesso**: 100% dos testes devem passar
- **Testes de regressão**: Executar antes de cada commit

### Integração Contínua
```yaml
# Exemplo para GitHub Actions
- name: Executar Testes
  run: |
    python run_tests.py --all --coverage
    coverage report --fail-under=80
```

## 🔧 Manutenção dos Testes

### Adicionando Novos Testes
1. Criar métodos de teste na classe apropriada
2. Usar factories para dados de teste
3. Seguir convenções de nomenclatura
4. Adicionar docstrings explicativas

### Atualizando Factories
1. Manter dados realistas
2. Usar Faker para dados variados
3. Garantir relacionamentos válidos
4. Documentar dependências

### Refatorando Testes
1. Extrair código comum para métodos helper
2. Usar setUp e tearDown adequadamente
3. Manter testes independentes
4. Evitar dependências entre testes

## 📚 Recursos Adicionais

### Documentação
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Selenium Python](https://selenium-python.readthedocs.io/)

### Ferramentas Úteis
- **pytest-django**: Integração Django + Pytest
- **factory-boy**: Criação de dados de teste
- **coverage**: Medição de cobertura de código
- **locust**: Testes de performance

### Boas Práticas
1. **AAA Pattern**: Arrange, Act, Assert
2. **Testes independentes**: Cada teste deve ser isolado
3. **Dados limpos**: Usar setUp/tearDown adequadamente
4. **Nomes descritivos**: Testes devem ser auto-explicativos
5. **Cobertura adequada**: Testar casos de sucesso e erro

## 🎉 Exemplo de Execução Completa

```bash
# 1. Instalar dependências
python run_tests.py --install

# 2. Executar todos os testes com cobertura
python run_tests.py --all --coverage

# 3. Verificar relatório de cobertura
open htmlcov/index.html

# 4. Executar testes específicos em modo verboso
python run_tests.py --module estoque --unit --verbose
```

---

**Nota**: Este guia é atualizado regularmente. Para dúvidas específicas, consulte a documentação do Django ou abra uma issue no repositório.
