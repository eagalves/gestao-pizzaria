from django.urls import path
from . import api_views

app_name = 'financeiro_api'

urlpatterns = [
    # Despesas
    path('despesas/', api_views.DespesasListView.as_view(), name='despesas_list'),
    path('despesas/criar/', api_views.DespesaCreateView.as_view(), name='despesa_create'),
    
    # Tipos de Despesa
    path('tipos-despesa/', api_views.TiposDespesaListView.as_view(), name='tipos_despesa_list'),
    
    # Metas de Venda
    path('metas-venda/', api_views.MetasVendaListView.as_view(), name='metas_venda_list'),
]
