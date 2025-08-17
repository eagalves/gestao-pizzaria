from django.contrib import admin
from .models import Cliente, EnderecoCliente


class EnderecoClienteInline(admin.TabularInline):
    model = EnderecoCliente
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email', 'pizzaria', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'pizzaria', 'data_cadastro')
    search_fields = ('nome', 'telefone', 'email')
    readonly_fields = ('data_cadastro', 'data_atualizacao')
    inlines = [EnderecoClienteInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('pizzaria', 'nome', 'telefone', 'email')
        }),
        ('Informações Adicionais', {
            'fields': ('data_nascimento', 'endereco_principal', 'observacoes')
        }),
        ('Controle', {
            'fields': ('ativo', 'data_cadastro', 'data_atualizacao')
        }),
    )


@admin.register(EnderecoCliente)
class EnderecoClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'rua', 'numero', 'bairro', 'cidade')
    list_filter = ('cidade', 'estado', 'bairro')
    search_fields = ('cliente__nome', 'rua', 'bairro', 'cidade')
    
    fieldsets = (
        ('Cliente', {
            'fields': ('cliente', 'nome')
        }),
        ('Endereço', {
            'fields': ('cep', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado')
        }),
        ('Referência', {
            'fields': ('referencia',)
        }),
    )