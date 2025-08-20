from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import TipoDespesa, DespesaOperacional, MovimentacaoCaixa, MetaVenda


@admin.register(TipoDespesa)
class TipoDespesaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    ordering = ['nome']


@admin.register(DespesaOperacional)
class DespesaOperacionalAdmin(admin.ModelAdmin):
    list_display = [
        'descricao', 'pizzaria', 'tipo_despesa', 'valor', 'tipo', 
        'data_vencimento', 'pago', 'recorrente'
    ]
    list_filter = [
        'pago', 'tipo', 'recorrente', 'tipo_despesa', 'forma_pagamento',
        'data_vencimento', 'pizzaria'
    ]
    search_fields = ['descricao', 'pizzaria__nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data_vencimento'
    ordering = ['-data_vencimento']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('pizzaria', 'tipo_despesa', 'descricao', 'valor_centavos', 'tipo')
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'data_vencimento', 'pago', 'data_pagamento')
        }),
        ('Recorrência', {
            'fields': ('recorrente', 'dia_vencimento_recorrente', 'data_inicio_recorrencia', 'data_fim_recorrencia'),
            'classes': ('collapse',)
        }),
        ('Outros', {
            'fields': ('observacoes', 'criado_em', 'atualizado_em')
        }),
    )


@admin.register(MovimentacaoCaixa)
class MovimentacaoCaixaAdmin(admin.ModelAdmin):
    list_display = [
        'descricao', 'pizzaria', 'tipo', 'origem', 'valor', 
        'forma_pagamento', 'data_movimentacao'
    ]
    list_filter = [
        'tipo', 'origem', 'forma_pagamento', 'data_movimentacao', 'pizzaria'
    ]
    search_fields = ['descricao', 'pizzaria__nome']
    readonly_fields = ['criado_em']
    date_hierarchy = 'data_movimentacao'
    ordering = ['-data_movimentacao']


@admin.register(MetaVenda)
class MetaVendaAdmin(admin.ModelAdmin):
    list_display = [
        'pizzaria', 'ano', 'mes', 'meta_receita', 'meta_ticket_medio'
    ]
    list_filter = ['ano', 'mes', 'pizzaria']
    search_fields = ['pizzaria__nome']
    ordering = ['-ano', '-mes']