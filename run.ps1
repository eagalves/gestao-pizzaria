# Script para ativar o ambiente virtual e executar o Django
Write-Host "=== Iniciando Gestão Pizzaria ===" -ForegroundColor Green

# Verificar se o ambiente virtual existe
if (-not (Test-Path "venv")) {
    Write-Host "Erro: Ambiente virtual 'venv' não encontrado!" -ForegroundColor Red
    Write-Host "Execute 'python -m venv venv' para criar o ambiente virtual." -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se o ambiente virtual já está ativado
if ($env:VIRTUAL_ENV) {
    Write-Host "Ambiente virtual já está ativado: $($env:VIRTUAL_ENV)" -ForegroundColor Green
} else {
    # Ativar o ambiente virtual
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Aviso: Não foi possível ativar o ambiente virtual." -ForegroundColor Yellow
        Write-Host "Continuando... (pode ser que já esteja ativado)" -ForegroundColor Yellow
    } else {
        Write-Host "Ambiente virtual ativado com sucesso!" -ForegroundColor Green
    }
}

# Verificar se as dependências estão instaladas
Write-Host "Verificando dependências..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\pip.exe")) {
    Write-Host "Erro: pip não encontrado no ambiente virtual!" -ForegroundColor Red
    pause
    exit 1
}

# Executar migrações se necessário
Write-Host "Verificando migrações..." -ForegroundColor Yellow
python manage.py migrate --check

# Iniciar o servidor Django
Write-Host "Iniciando servidor Django..." -ForegroundColor Green
Write-Host "Acesse: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

python manage.py runserver
