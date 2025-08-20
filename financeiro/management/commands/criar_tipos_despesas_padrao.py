from django.core.management.base import BaseCommand
from financeiro.models import TipoDespesa


class Command(BaseCommand):
    help = 'Cria tipos de despesas padrão para pizzarias'

    def handle(self, *args, **options):
        tipos_despesas = [
            {
                'nome': 'Aluguel',
                'descricao': 'Aluguel do imóvel onde funciona a pizzaria'
            },
            {
                'nome': 'Energia Elétrica',
                'descricao': 'Conta de energia elétrica'
            },
            {
                'nome': 'Água',
                'descricao': 'Conta de água e esgoto'
            },
            {
                'nome': 'Internet/Telefone',
                'descricao': 'Serviços de internet e telefonia'
            },
            {
                'nome': 'Salários',
                'descricao': 'Pagamento de funcionários'
            },
            {
                'nome': 'Encargos Trabalhistas',
                'descricao': 'INSS, FGTS e outros encargos'
            },
            {
                'nome': 'Impostos',
                'descricao': 'Impostos diversos (ISS, ICMS, etc.)'
            },
            {
                'nome': 'Delivery',
                'descricao': 'Taxa de plataformas de delivery (iFood, Uber Eats, etc.)'
            },
            {
                'nome': 'Embalagens',
                'descricao': 'Caixas de pizza, sacolas, guardanapos, etc.'
            },
            {
                'nome': 'Marketing',
                'descricao': 'Publicidade e marketing'
            },
            {
                'nome': 'Manutenção',
                'descricao': 'Manutenção de equipamentos e instalações'
            },
            {
                'nome': 'Combustível',
                'descricao': 'Combustível para delivery próprio'
            },
            {
                'nome': 'Limpeza',
                'descricao': 'Produtos de limpeza e higiene'
            },
            {
                'nome': 'Seguros',
                'descricao': 'Seguros diversos (incêndio, roubo, etc.)'
            },
            {
                'nome': 'Contabilidade',
                'descricao': 'Serviços contábeis'
            },
            {
                'nome': 'Outros',
                'descricao': 'Outras despesas operacionais'
            }
        ]
        
        criados = 0
        for tipo_data in tipos_despesas:
            tipo, created = TipoDespesa.objects.get_or_create(
                nome=tipo_data['nome'],
                defaults={'descricao': tipo_data['descricao']}
            )
            if created:
                criados += 1
                self.stdout.write(f'Criado: {tipo.nome}')
            else:
                self.stdout.write(f'Já existe: {tipo.nome}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Processo concluído! {criados} tipos de despesas criados.')
        )
