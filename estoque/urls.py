from django.urls import path
from . import views

app_name = 'estoque'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_estoque, name='dashboard_estoque'),
    
    # Estoque
    path('estoque/', views.lista_estoque, name='lista_estoque'),
    path('estoque/pizzaria/<int:pizzaria_id>/', views.lista_estoque, name='lista_estoque_pizzaria'),
    path('estoque/<int:estoque_id>/editar/', views.editar_estoque, name='editar_estoque'),
    
    # Fornecedores
    path('fornecedores/', views.lista_fornecedores, name='lista_fornecedores'),
    path('fornecedores/adicionar/', views.adicionar_fornecedor, name='adicionar_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/editar/', views.editar_fornecedor, name='editar_fornecedor'),
    
    # Compras
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/registrar/', views.registrar_compra, name='registrar_compra'),
    
    # Relatórios
    path('relatorios/custos/', views.relatorio_custos, name='relatorio_custos'),
    path('ingredientes/<int:ingrediente_id>/historico/', views.historico_precos, name='historico_precos'),

    # Histórico de utilização
    path('usos/', views.historico_uso_estoque, name='historico_uso_estoque'),
    path('ingredientes/<int:ingrediente_id>/usos/', views.historico_uso_ingrediente, name='historico_uso_ingrediente'),
    
    # AJAX
    path('ajax/ingrediente/<int:ingrediente_id>/preco/', views.ajax_ingrediente_preco, name='ajax_ingrediente_preco'),
]
