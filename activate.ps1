# Script para ativar o ambiente virtual
# Verificar se o ambiente virtual já está ativado
if ($env:VIRTUAL_ENV) {
    Write-Host "Ambiente virtual já está ativado: $($env:VIRTUAL_ENV)" -ForegroundColor Green
} else {
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Ambiente virtual ativado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "Aviso: Não foi possível ativar o ambiente virtual." -ForegroundColor Yellow
        Write-Host "Pode ser que já esteja ativado ou haja algum problema." -ForegroundColor Yellow
    }
}

Write-Host "Agora você pode executar comandos como:" -ForegroundColor Cyan
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host "  python manage.py migrate" -ForegroundColor White
Write-Host "  python manage.py makemigrations" -ForegroundColor White
