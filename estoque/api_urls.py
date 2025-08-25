from django.urls import path
from . import api_views

app_name = 'estoque_api'

urlpatterns = [
    # Estoque
    path('estoque/', api_views.EstoqueListView.as_view(), name='estoque_list'),
    path('estoque/criar/', api_views.EstoqueCreateView.as_view(), name='estoque_create'),
    
    # Fornecedores
    path('fornecedores/', api_views.FornecedoresListView.as_view(), name='fornecedores_list'),
    
    # Compras
    path('compras/', api_views.ComprasListView.as_view(), name='compras_list'),
]
