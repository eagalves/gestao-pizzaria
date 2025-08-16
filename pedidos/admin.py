from django.contrib import admin

from .models import Pedido, ItemPedido

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pizzaria", "cliente_nome", "status", "total", "data_criacao")
    list_filter = ("status", "pizzaria")
    inlines = [ItemPedidoInline]
