# Use Python oficial
FROM python:3.13.5

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema (se precisar)
RUN apt-get update && apt-get install -y postgresql-client

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando default
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]