from django.core.management.base import BaseCommand
from financeiro.models import TipoDespesa


class Command(BaseCommand):
    help = 'Cria tipos de despesa padrão para o sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== CRIANDO TIPOS DE DESPESA PADRÃO ==='))
        
        tipos_padrao = [
            {
                'nome': 'Aluguel',
                'descricao': 'Aluguel do imóvel comercial'
            },
            {
                'nome': 'Luz',
                'descricao': 'Conta de energia elétrica'
            },
            {
                'nome': 'Água',
                'descricao': 'Conta de água e esgoto'
            },
            {
                'nome': 'Internet',
                'descricao': 'Serviço de internet e telefone'
            },
            {
                'nome': 'Gás',
                'descricao': 'Conta de gás encanado ou botijão'
            },
            {
                'nome': 'Manutenção',
                'descricao': 'Manutenção de equipamentos e estrutura'
            },
            {
                'nome': 'Marketing',
                'descricao': 'Publicidade, panfletos e divulgação'
            },
            {
                'nome': 'Impostos',
                'descricao': 'Tributos, taxas e contribuições'
            },
            {
                'nome': 'Limpeza',
                'descricao': 'Material de limpeza e serviços'
            },
            {
                'nome': 'Segurança',
                'descricao': 'Sistemas de segurança e vigilância'
            },
            {
                'nome': 'Funcionários',
                'descricao': 'Salários, benefícios e encargos'
            },
            {
                'nome': 'Fornecedores',
                'descricao': 'Pagamentos a fornecedores diversos'
            }
        ]
        
        criados = 0
        existentes = 0
        
        for tipo_data in tipos_padrao:
            tipo, created = TipoDespesa.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={
                    'descricao': tipo_data['descricao'],
                    'ativo': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Criado: {tipo.nome}')
                )
                criados += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Já existe: {tipo.nome}')
                )
                existentes += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n=== RESUMO ==='))
        self.stdout.write(f'Tipos criados: {criados}')
        self.stdout.write(f'Tipos existentes: {existentes}')
        self.stdout.write(f'Total: {criados + existentes}')
        
        if criados > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 {criados} tipos de despesa foram criados com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\nℹ️  Todos os tipos de despesa padrão já existem no sistema.')
            )
