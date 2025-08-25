# 📚 Documentação da API com Swagger

Este projeto agora inclui documentação completa da API usando **drf-spectacular** (Swagger/OpenAPI 3.0).

## 🚀 Como Acessar

### 1. **Swagger UI (Interface Interativa)**
```
http://localhost:8000/api/docs/
```

### 2. **ReDoc (Documentação Alternativa)**
```
http://localhost:8000/api/redoc/
```

### 3. **Schema OpenAPI (JSON)**
```
http://localhost:8000/api/schema/
```

## 📋 Endpoints Documentados

### 🔐 **Autenticação**
- **Base URL**: `/api/v1/`
- **Tag**: `autenticacao`

#### Endpoints:
- `GET /api/v1/pizzarias/` - Listar todas as pizzarias
- `POST /api/v1/pizzarias/criar/` - Cadastrar nova pizzaria
- `GET /api/v1/pizzarias/{id}/` - Detalhes de uma pizzaria
- `GET /api/v1/dashboard/super-admin/` - Dashboard Super Admin

### 🍕 **Produtos**
- **Tag**: `produtos`

#### Endpoints:
- `GET /api/v1/produtos/` - Listar todos os produtos
- `POST /api/v1/produtos/criar/` - Cadastrar novo produto

### 🏷️ **Categorias**
- **Tag**: `categorias`

#### Endpoints:
- `GET /api/v1/categorias/` - Listar todas as categorias
- `POST /api/v1/categorias/criar/` - Cadastrar nova categoria

### 👥 **Clientes**
- **Tag**: `clientes`

#### Endpoints:
- `GET /api/v1/clientes/` - Listar todos os clientes
- `POST /api/v1/clientes/criar/` - Cadastrar novo cliente
- `GET /api/v1/clientes/{id}/enderecos/` - Endereços de um cliente

### 📦 **Estoque**
- **Tag**: `estoque`

#### Endpoints:
- `GET /api/v1/estoque/` - Listar itens do estoque
- `POST /api/v1/estoque/criar/` - Cadastrar novo item

### 🏪 **Fornecedores**
- **Tag**: `fornecedores`

#### Endpoints:
- `GET /api/v1/fornecedores/` - Listar todos os fornecedores

### 🛒 **Compras**
- **Tag**: `compras`

#### Endpoints:
- `GET /api/v1/compras/` - Listar todas as compras

### 💰 **Financeiro**
- **Tag**: `financeiro`

#### Endpoints:
- `GET /api/v1/despesas/` - Listar todas as despesas
- `POST /api/v1/despesas/criar/` - Cadastrar nova despesa
- `GET /api/v1/tipos-despesa/` - Listar tipos de despesa
- `GET /api/v1/metas-venda/` - Listar metas de venda

### 📋 **Pedidos**
- **Tag**: `pedidos`

#### Endpoints:
- `GET /api/v1/pedidos/` - Listar todos os pedidos
- `POST /api/v1/pedidos/criar/` - Cadastrar novo pedido
- `GET /api/v1/pedidos/{id}/` - Detalhes de um pedido

### 🥘 **Ingredientes**
- **Tag**: `ingredientes`

#### Endpoints:
- `GET /api/v1/ingredientes/` - Listar todos os ingredientes
- `POST /api/v1/ingredientes/criar/` - Cadastrar novo ingrediente
- `GET /api/v1/ingredientes/{id}/` - Detalhes de um ingrediente

## 🔑 **Autenticação**

Todos os endpoints requerem autenticação via **Session Authentication** do Django.

### Como Testar:

1. **Faça login** no sistema Django (`/admin/` ou interface de login)
2. **Acesse o Swagger** em `/api/docs/`
3. **Clique em "Authorize"** (ícone de cadeado)
4. **Use suas credenciais** do Django
5. **Teste os endpoints** diretamente na interface

## 🛠️ **Configurações do Swagger**

### Arquivo: `meu_projeto/settings.py`

```python
# Configurações do Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Configurações do drf-spectacular (Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'API de Gestão de Pizzarias',
    'DESCRIPTION': 'API completa para gerenciamento de pizzarias...',
    'VERSION': '1.0.0',
    'TAGS': [
        {'name': 'autenticacao', 'description': 'Endpoints de autenticação...'},
        {'name': 'pizzarias', 'description': 'Gerenciamento de pizzarias...'},
        # ... outros tags
    ],
}
```

## 📁 **Estrutura dos Arquivos**

```
app/
├── api_views.py          # Views da API com decoradores @extend_schema
├── api_urls.py           # URLs da API
├── forms.py              # Formulários para validação
├── models.py             # Modelos do banco de dados
└── views.py              # Views tradicionais do Django
```

## 🎯 **Recursos do Swagger**

### ✅ **Funcionalidades Implementadas:**
- **Documentação automática** de todos os endpoints
- **Esquemas de request/response** detalhados
- **Exemplos de uso** para cada endpoint
- **Validação de parâmetros** e tipos de dados
- **Interface interativa** para testes
- **Tags organizadas** por funcionalidade
- **Descrições detalhadas** de cada operação

### 🔧 **Decoradores Utilizados:**
- `@extend_schema` - Documentação principal
- `OpenApiParameter` - Parâmetros de URL
- `OpenApiExample` - Exemplos de uso
- **Tags personalizadas** para organização

## 🚀 **Próximos Passos**

### **Melhorias Sugeridas:**
1. **Adicionar mais endpoints** para operações CRUD completas
2. **Implementar filtros** e paginação
3. **Adicionar validações** customizadas
4. **Implementar rate limiting**
5. **Adicionar testes** automatizados para a API

### **Endpoints Faltantes:**
- **PUT/PATCH** para atualização
- **DELETE** para exclusão
- **Filtros** por data, status, etc.
- **Relatórios** e estatísticas

## 📖 **Referências**

- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)
- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

**🎉 Sua API agora está completamente documentada com Swagger!**
