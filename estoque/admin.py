from django.contrib import admin
from .models import Fornecedor, EstoqueIngrediente, CompraIngrediente, HistoricoPrecoCompra

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'telefone', 'ativo', 'pizzaria']
    list_filter = ['ativo', 'pizzaria']
    search_fields = ['nome', 'cnpj']

@admin.register(EstoqueIngrediente)
class EstoqueIngredienteAdmin(admin.ModelAdmin):
    list_display = ['ingrediente', 'quantidade_atual', 'unidade_medida', 'estoque_minimo', 'get_preco_compra']
    list_filter = ['ingrediente__pizzaria', 'unidade_medida']
    search_fields = ['ingrediente__nome']
    
    def get_preco_compra(self, obj):
        return f"R$ {obj.preco_compra_atual_centavos / 100:.2f}"
    get_preco_compra.short_description = 'Preço Atual'

@admin.register(CompraIngrediente)
class CompraIngredienteAdmin(admin.ModelAdmin):
    list_display = ['ingrediente', 'fornecedor', 'quantidade', 'get_preco_unitario', 'data_compra']
    list_filter = ['data_compra', 'fornecedor']
    search_fields = ['ingrediente__nome', 'fornecedor__nome']
    
    def get_preco_unitario(self, obj):
        return f"R$ {obj.preco_unitario_centavos / 100:.2f}"
    get_preco_unitario.short_description = 'Preço Unitário'

@admin.register(HistoricoPrecoCompra)
class HistoricoPrecoCompraAdmin(admin.ModelAdmin):
    list_display = ['ingrediente', 'get_preco', 'data_preco', 'fornecedor']
    list_filter = ['data_preco', 'fornecedor']
    search_fields = ['ingrediente__nome']
    
    def get_preco(self, obj):
        return f"R$ {obj.preco_centavos / 100:.2f}"
    get_preco.short_description = 'Preço'
