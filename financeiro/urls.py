from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.dashboard_financeiro, name='dashboard'),
    path('relatorio-vendas/', views.relatorio_vendas, name='relatorio_vendas'),
    path('relatorio-custos/', views.relatorio_custos, name='relatorio_custos'),
    path('fluxo-caixa/', views.fluxo_caixa, name='fluxo_caixa'),
    path('metas-vendas/', views.metas_vendas, name='metas_vendas'),
    path('despesas-operacionais/', views.despesas_operacionais, name='despesas_operacionais'),
    
    # Gestão de Despesas Operacionais
    path('despesas-operacionais/adicionar/', views.adicionar_despesa, name='adicionar_despesa'),
    path('despesas-operacionais/<int:despesa_id>/editar/', views.editar_despesa, name='editar_despesa'),
    path('despesas-operacionais/<int:despesa_id>/excluir/', views.excluir_despesa, name='excluir_despesa'),
    path('despesas-operacionais/<int:despesa_id>/marcar-paga/', views.marcar_despesa_paga, name='marcar_despesa_paga'),
    
    # Gestão de Tipos de Despesa
    path('tipos-despesa/adicionar/', views.adicionar_tipo_despesa, name='adicionar_tipo_despesa'),
]
