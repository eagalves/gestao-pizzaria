#!/usr/bin/env python
"""
Script para executar testes do projeto de gestão de pizzaria.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Executa um comando e exibe o resultado."""
    print(f"\n{'='*60}")
    print(f"Executando: {description}")
    print(f"Comando: {command}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar: {e}")
        print(f"Stderr: {e.stderr}")
        return False


def run_unit_tests(module=None, verbose=False):
    """Executa testes unitários."""
    if module:
        command = f"python manage.py test {module}.tests"
    else:
        command = "python manage.py test"
    
    if verbose:
        command += " -v 2"
    
    return run_command(command, "Testes Unitários")


def run_pytest_tests(module=None, coverage=False, parallel=False):
    """Executa testes usando pytest."""
    command = "pytest"
    
    if module:
        command += f" {module}/"
    
    if coverage:
        command += " --cov --cov-report=html --cov-report=term-missing"
    
    if parallel:
        command += " -n auto"
    
    command += " -v"
    
    return run_command(command, "Testes com Pytest")


def run_coverage():
    """Executa cobertura de código."""
    commands = [
        ("coverage run --source='.' manage.py test", "Executando testes com cobertura"),
        ("coverage report", "Relatório de cobertura"),
        ("coverage html", "Gerando relatório HTML de cobertura")
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success


def run_e2e_tests():
    """Executa testes end-to-end."""
    # Verificar se Selenium está disponível
    try:
        import selenium
        print("Selenium disponível. Executando testes E2E...")
        
        command = "python manage.py test estoque.test_e2e -v 2"
        return run_command(command, "Testes End-to-End")
    except ImportError:
        print("Selenium não disponível. Instale com: pip install selenium")
        return False


def run_performance_tests():
    """Executa testes de performance."""
    try:
        import locust
        print("Locust disponível. Executando testes de performance...")
        
        # Aqui você pode adicionar comandos específicos para testes de performance
        print("Testes de performance configurados para execução manual.")
        return True
    except ImportError:
        print("Locust não disponível. Instale com: pip install locust")
        return False


def install_test_dependencies():
    """Instala dependências de teste."""
    command = "pip install -r requirements-test.txt"
    return run_command(command, "Instalando dependências de teste")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Script de execução de testes")
    parser.add_argument("--module", "-m", help="Módulo específico para testar")
    parser.add_argument("--unit", action="store_true", help="Executar testes unitários")
    parser.add_argument("--pytest", action="store_true", help="Executar testes com pytest")
    parser.add_argument("--e2e", action="store_true", help="Executar testes end-to-end")
    parser.add_argument("--coverage", action="store_true", help="Executar com cobertura")
    parser.add_argument("--performance", action="store_true", help="Executar testes de performance")
    parser.add_argument("--install", action="store_true", help="Instalar dependências de teste")
    parser.add_argument("--all", action="store_true", help="Executar todos os testes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    parser.add_argument("--parallel", "-p", action="store_true", help="Executar testes em paralelo")
    
    args = parser.parse_args()
    
    # Verificar se estamos no diretório correto
    if not Path("manage.py").exists():
        print("Erro: execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    success = True
    
    # Instalar dependências se solicitado
    if args.install:
        success = install_test_dependencies() and success
    
    # Executar todos os testes se solicitado
    if args.all:
        print("Executando todos os testes...")
        success = run_unit_tests(verbose=args.verbose) and success
        success = run_pytest_tests(coverage=True, parallel=args.parallel) and success
        success = run_e2e_tests() and success
        success = run_performance_tests() and success
        success = run_coverage() and success
    else:
        # Executar testes específicos
        if args.unit:
            success = run_unit_tests(args.module, args.verbose) and success
        
        if args.pytest:
            success = run_pytest_tests(args.module, args.coverage, args.parallel) and success
        
        if args.e2e:
            success = run_e2e_tests() and success
        
        if args.performance:
            success = run_performance_tests() and success
        
        if args.coverage:
            success = run_coverage() and success
        
        # Se nenhum tipo específico foi selecionado, executar testes unitários padrão
        if not any([args.unit, args.pytest, args.e2e, args.performance, args.coverage]):
            success = run_unit_tests(args.module, args.verbose) and success
    
    # Resumo final
    print(f"\n{'='*60}")
    if success:
        print("✅ Todos os testes executados com sucesso!")
    else:
        print("❌ Alguns testes falharam. Verifique os erros acima.")
    print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
