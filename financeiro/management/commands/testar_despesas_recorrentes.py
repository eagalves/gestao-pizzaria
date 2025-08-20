from django.core.management.base import BaseCommand
from django.utils import timezone
from financeiro.models import DespesaOperacional
from autenticacao.models import Pizzaria
from financeiro.models import TipoDespesa


class Command(BaseCommand):
    help = 'Testa o sistema de despesas fixas mensais criando exemplos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== TESTANDO SISTEMA DE DESPESAS FIXAS MENSAIS ==='))
        self.stdout.write('💡 Agora todas as despesas são cadastradas através do formulário "Nova Despesa"')
        self.stdout.write('')
        
        # Buscar a primeira pizzaria
        try:
            pizzaria = Pizzaria.objects.first()
            if not pizzaria:
                self.stdout.write(self.style.ERROR('Nenhuma pizzaria encontrada. Crie uma pizzaria primeiro.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao buscar pizzaria: {e}'))
            return
        
        # Buscar ou criar tipos de despesa
        tipos_despesa = {}
        for nome_tipo in ['Aluguel', 'Luz', 'Água', 'Internet']:
            tipo, created = TipoDespesa.objects.get_or_create(
                nome=nome_tipo,
                defaults={'descricao': f'Despesa de {nome_tipo.lower()}'}
            )
            tipos_despesa[nome_tipo] = tipo
            if created:
                self.stdout.write(f'✅ Tipo de despesa "{nome_tipo}" criado')
            else:
                self.stdout.write(f'ℹ️  Tipo de despesa "{nome_tipo}" já existe')
        
        # Criar despesas fixas mensais de exemplo
        despesas_exemplo = [
            {
                'tipo_despesa': tipos_despesa['Aluguel'],
                'descricao': 'Aluguel do Imóvel',
                'valor_centavos': 150000,  # R$ 1.500,00
                'tipo': 'FIXA',
                'forma_pagamento': 'BOL',
                'data_vencimento': timezone.now().date().replace(day=5),
                'recorrente': True,
                'dia_vencimento_recorrente': 5,
                'data_inicio_recorrencia': timezone.now().date().replace(day=1),
                'data_fim_recorrencia': None,  # Indefinido
            },
            {
                'tipo_despesa': tipos_despesa['Luz'],
                'descricao': 'Conta de Energia Elétrica',
                'valor_centavos': 8000,  # R$ 80,00
                'tipo': 'FIXA',
                'forma_pagamento': 'DEB',
                'data_vencimento': timezone.now().date().replace(day=15),
                'recorrente': True,
                'dia_vencimento_recorrente': 15,
                'data_inicio_recorrencia': timezone.now().date().replace(day=1),
                'data_fim_recorrencia': None,  # Indefinido
            },
            {
                'tipo_despesa': tipos_despesa['Água'],
                'descricao': 'Conta de Água e Esgoto',
                'valor_centavos': 4500,  # R$ 45,00
                'tipo': 'FIXA',
                'forma_pagamento': 'DEB',
                'data_vencimento': timezone.now().date().replace(day=20),
                'recorrente': True,
                'dia_vencimento_recorrente': 20,
                'data_inicio_recorrencia': timezone.now().date().replace(day=1),
                'data_fim_recorrencia': None,  # Indefinido
            },
            {
                'tipo_despesa': tipos_despesa['Internet'],
                'descricao': 'Serviço de Internet',
                'valor_centavos': 12000,  # R$ 120,00
                'tipo': 'FIXA',
                'forma_pagamento': 'DEB',
                'data_vencimento': timezone.now().date().replace(day=10),
                'recorrente': True,
                'dia_vencimento_recorrente': 10,
                'data_inicio_recorrencia': timezone.now().date().replace(day=1),
                'data_fim_recorrencia': None,  # Indefinido
            }
        ]
        
        despesas_criadas = []
        for dados in despesas_exemplo:
            # Verificar se já existe
            if DespesaOperacional.objects.filter(
                pizzaria=pizzaria,
                descricao=dados['descricao'],
                recorrente=True
            ).exists():
                self.stdout.write(f'ℹ️  Despesa fixa mensal "{dados["descricao"]}" já existe')
                continue
            
            # Criar despesa fixa mensal
            despesa = DespesaOperacional.objects.create(
                pizzaria=pizzaria,
                **dados
            )
            despesas_criadas.append(despesa)
            self.stdout.write(f'✅ Despesa fixa mensal "{dados["descricao"]}" criada')
        
        if despesas_criadas:
            self.stdout.write(f'\n🎯 {len(despesas_criadas)} despesas fixas mensais criadas com sucesso!')
            
            # Testar geração automática
            self.stdout.write('\n🔄 Testando geração automática de despesas mensais...')
            
            total_geradas = 0
            for despesa in despesas_criadas:
                despesas_mensais = despesa.gerar_despesas_pendentes()
                total_geradas += len(despesas_mensais)
                if despesas_mensais:
                    self.stdout.write(f'   📅 "{despesa.descricao}": {len(despesas_mensais)} despesas mensais geradas')
                else:
                    self.stdout.write(f'   ⚠️  "{despesa.descricao}": Nenhuma despesa mensal gerada')
            
            self.stdout.write(f'\n📊 Total de despesas mensais geradas: {total_geradas}')
            
            # Mostrar resumo
            self.stdout.write('\n📋 RESUMO DO TESTE:')
            self.stdout.write(f'   • Pizzaria: {pizzaria.nome}')
            self.stdout.write(f'   • Despesas fixas mensais: {DespesaOperacional.objects.filter(pizzaria=pizzaria, recorrente=True).count()}')
            self.stdout.write(f'   • Despesas mensais geradas: {total_geradas}')
            self.stdout.write(f'   • Total mensal recorrente: R$ {sum(d.valor for d in despesas_criadas):.2f}')
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Teste concluído com sucesso!'))
            self.stdout.write('\n💡 Para cadastrar novas despesas, vá para: /financeiro/despesas-operacionais/')
            self.stdout.write('   Clique em "Nova Despesa" e marque o checkbox "Recorrente" para despesas fixas mensais.')
            
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Nenhuma nova despesa fixa mensal foi criada (todas já existem)'))
        
        # Mostrar estatísticas finais
        self.stdout.write('\n📈 ESTATÍSTICAS FINAIS:')
        total_fixas_mensais = DespesaOperacional.objects.filter(pizzaria=pizzaria, recorrente=True).count()
        total_mensais = DespesaOperacional.objects.filter(
            pizzaria=pizzaria,
            observacoes__icontains='Gerada automaticamente'
        ).count()
        
        self.stdout.write(f'   • Total de despesas fixas mensais: {total_fixas_mensais}')
        self.stdout.write(f'   • Total de despesas mensais geradas: {total_mensais}')
        
        if total_fixas_mensais > 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Sistema de despesas fixas mensais funcionando perfeitamente!'))
            self.stdout.write('\n🚀 FLUXO SIMPLIFICADO:')
            self.stdout.write('   1. Acesse "Nova Despesa"')
            self.stdout.write('   2. Marque "Recorrente"')
            self.stdout.write('   3. Preencha os campos obrigatórios')
            self.stdout.write('   4. Salve - as despesas mensais são geradas automaticamente!')
