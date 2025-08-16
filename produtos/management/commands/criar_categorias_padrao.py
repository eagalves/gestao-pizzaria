from django.core.management.base import BaseCommand
from autenticacao.models import Pizzaria
from produtos.models import CategoriaProduto


class Command(BaseCommand):
    help = 'Cria categorias padrão para todas as pizzarias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pizzaria-id',
            type=int,
            help='ID da pizzaria específica (opcional)',
        )

    def handle(self, *args, **options):
        categorias_padrao = [
            ('Pizzas Tradicionais', 1),
            ('Pizzas Especiais', 2),
            ('Pizzas Doces', 3),
            ('Bebidas', 4),
            ('Massas', 5),
            ('Porções', 6),
            ('Sobremesas', 7),
            ('Lanches', 8),
        ]

        if options['pizzaria_id']:
            pizzarias = Pizzaria.objects.filter(id=options['pizzaria_id'])
        else:
            pizzarias = Pizzaria.objects.all()

        for pizzaria in pizzarias:
            self.stdout.write(f'Criando categorias para: {pizzaria.nome}')
            
            for nome, ordem in categorias_padrao:
                categoria, created = CategoriaProduto.objects.get_or_create(
                    pizzaria=pizzaria,
                    nome=nome,
                    defaults={'ordem': ordem}
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Categoria "{nome}" criada')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  - Categoria "{nome}" já existe')
                    )

        self.stdout.write(
            self.style.SUCCESS('Comando executado com sucesso!')
        )
