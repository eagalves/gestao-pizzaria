from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import TipoDespesa, DespesaOperacional, MovimentacaoCaixa, MetaVenda


@admin.register(TipoDespesa)
class TipoDespesaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'total_despesas')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')
    
    def total_despesas(self, obj):
        """Mostra total de despesas deste tipo."""
        total = obj.despesas.filter(pago=False).count()
        return f"{total} pendentes"
    total_despesas.short_description = "Despesas"


@admin.register(DespesaOperacional)
class DespesaOperacionalAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'pizzaria', 'tipo', 'valor_formatado', 'data_vencimento', 'status_pagamento', 'em_atraso')
    list_filter = ('pizzaria', 'tipo', 'pago', 'tipo_despesa', 'forma_pagamento')
    search_fields = ('descricao', 'observacoes')
    date_hierarchy = 'data_vencimento'
    ordering = ['-data_vencimento']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('pizzaria', 'tipo_despesa', 'descricao', 'tipo')
        }),
        ('Valores', {
            'fields': ('valor_centavos',)
        }),
        ('Datas e Pagamento', {
            'fields': ('data_vencimento', 'forma_pagamento', 'pago', 'data_pagamento')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    def valor_formatado(self, obj):
        """Mostra valor formatado em reais."""
        return f"R$ {obj.valor:.2f}"
    valor_formatado.short_description = "Valor"
    valor_formatado.admin_order_field = 'valor_centavos'
    
    def status_pagamento(self, obj):
        """Mostra status visual do pagamento."""
        if obj.pago:
            return format_html('<span style="color: green;">✓ Pago</span>')
        else:
            return format_html('<span style="color: red;">✗ Pendente</span>')
    status_pagamento.short_description = "Status"
    status_pagamento.admin_order_field = 'pago'
    
    def em_atraso(self, obj):
        """Indica se está em atraso."""
        if obj.em_atraso:
            return format_html('<span style="color: red; font-weight: bold;">SIM</span>')
        return "Não"
    em_atraso.short_description = "Em Atraso"
    
    actions = ['marcar_como_pagas']
    
    def marcar_como_pagas(self, request, queryset):
        """Marca despesas selecionadas como pagas."""
        count = 0
        for despesa in queryset.filter(pago=False):
            despesa.marcar_como_paga()
            count += 1
        
        self.message_user(request, f"{count} despesas marcadas como pagas.")
    marcar_como_pagas.short_description = "Marcar como pagas"


@admin.register(MovimentacaoCaixa)
class MovimentacaoCaixaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'pizzaria', 'tipo', 'origem', 'valor_com_sinal_formatado', 'forma_pagamento', 'data_movimentacao')
    list_filter = ('pizzaria', 'tipo', 'origem', 'forma_pagamento')
    search_fields = ('descricao', 'observacoes')
    date_hierarchy = 'data_movimentacao'
    ordering = ['-data_movimentacao']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('pizzaria', 'tipo', 'origem', 'descricao')
        }),
        ('Valores', {
            'fields': ('valor_centavos', 'forma_pagamento')
        }),
        ('Data', {
            'fields': ('data_movimentacao',)
        }),
        ('Referências', {
            'fields': ('pedido', 'despesa', 'compra_estoque'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    def valor_com_sinal_formatado(self, obj):
        """Mostra valor com sinal formatado."""
        valor = obj.valor_com_sinal
        cor = "green" if valor > 0 else "red"
        sinal = "+" if valor > 0 else ""
        return format_html(f'<span style="color: {cor}; font-weight: bold;">{sinal}R$ {abs(valor):.2f}</span>')
    valor_com_sinal_formatado.short_description = "Valor"
    valor_com_sinal_formatado.admin_order_field = 'valor_centavos'


@admin.register(MetaVenda)
class MetaVendaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pizzaria', 'mes_ano', 'tipo_meta', 'categoria', 'ativo', 'percentual_realizacao')
    list_filter = ('pizzaria', 'tipo_meta', 'ativo', 'ano', 'categoria')
    search_fields = ('nome', 'observacoes')
    ordering = ['-ano', '-mes']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('pizzaria', 'nome', 'tipo_meta', 'categoria')
        }),
        ('Período', {
            'fields': ('mes', 'ano')
        }),
        ('Metas', {
            'fields': ('meta_receita_centavos', 'meta_quantidade', 'meta_ticket_medio_centavos')
        }),
        ('Controle', {
            'fields': ('ativo', 'observacoes')
        })
    )
    
    def mes_ano(self, obj):
        """Mostra mês/ano formatado."""
        return f"{obj.mes:02d}/{obj.ano}"
    mes_ano.short_description = "Período"
    mes_ano.admin_order_field = ['ano', 'mes']
    
    def percentual_realizacao(self, obj):
        """Mostra percentual de realização da meta."""
        try:
            realizacao = obj.calcular_realizacao()
            
            if obj.tipo_meta == 'RECEITA':
                percentual = realizacao['percentual_receita']
            elif obj.tipo_meta == 'QUANTIDADE':
                percentual = realizacao['percentual_quantidade']
            else:  # TICKET
                percentual = realizacao['percentual_ticket']
            
            if percentual >= 100:
                cor = "green"
            elif percentual >= 80:
                cor = "orange"
            else:
                cor = "red"
            
            return format_html(f'<span style="color: {cor}; font-weight: bold;">{percentual:.1f}%</span>')
        except:
            return "Erro no cálculo"
    percentual_realizacao.short_description = "Realização"