- # Dockerfile vs Docker-Compose

## 🎯 Diferença Principal

| **Dockerfile** | **Docker-Compose** |
|----------------|-------------------|
| 📋 **Receita** para criar 1 imagem | 🎭 **Maestro** que coordena N containers |
| Como **construir** | Como **orquestrar** |

## 📄 Dockerfile
- **Propósito**: Criar uma imagem Docker customizada
- **Escopo**: 1 serviço/aplicação apenas  
- **Resultado**: Imagem (template/molde)
- **Comando**: `docker build -t nome .`
- **Exemplo**:
```dockerfile
FROM python:3.9
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver"]
```

## 🎼 Docker-Compose
- **Propósito**: Orquestrar múltiplos containers
- **Escopo**: Aplicação completa (web + banco + cache + etc)
- **Resultado**: Aplicação funcionando
- **Comando**: `docker-compose up`
- **Exemplo**:
```yaml
services:
  web:
    build: .              # ← Usa Dockerfile
  db:
    image: postgres:13    # ← Usa imagem pronta
```

## 🔄 Como Trabalham Juntos

1. **Dockerfile** cria imagem customizada (ex: Django)
2. **Docker-Compose** usa essa imagem + outras (ex: PostgreSQL)
3. **Resultado**: Aplicação completa rodando

## 💡 Analogia
- **Dockerfile** = Receita de um prato
- **Docker-Compose** = Menu completo do restaurante

## 🎯 Quando Usar

### Dockerfile
- ✅ Criar ambiente customizado
- ✅ Instalar dependências específicas  
- ✅ 1 serviço apenas

### Docker-Compose  
- ✅ Múltiplos serviços (web + db + cache)
- ✅ Desenvolvimento local
- ✅ Aplicação completa

---
**Resumo**: Dockerfile constrói, Docker-Compose orquestra! 🚀