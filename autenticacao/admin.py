from django.contrib import admin
from .models import Pizzaria, UsuarioPizzaria


@admin.register(Pizzaria)
class PizzariaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "telefone", "ativa", "criada_em")
    list_filter = ("ativa",)
    search_fields = ("nome", "cnpj")


@admin.register(UsuarioPizzaria)
class UsuarioPizzariaAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "pizzaria",
        "papel",
        "ativo",
        "criado_em",
    )
    list_filter = ("papel", "ativo", "pizzaria")
    search_fields = (
        "usuario__username",
        "usuario__email",
        "pizzaria__nome",
    )
