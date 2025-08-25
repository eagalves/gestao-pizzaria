from django.urls import path
from . import api_views

app_name = 'clientes_api'

urlpatterns = [
    # Clientes
    path('clientes/', api_views.ClientesListView.as_view(), name='clientes_list'),
    path('clientes/criar/', api_views.ClienteCreateView.as_view(), name='cliente_create'),
    
    # Endereços
    path('clientes/<int:cliente_id>/enderecos/', api_views.ClienteEnderecosView.as_view(), name='cliente_enderecos'),
]
