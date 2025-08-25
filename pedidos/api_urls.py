from django.urls import path
from . import api_views

app_name = 'pedidos_api'

urlpatterns = [
    # Pedidos
    path('pedidos/', api_views.PedidosListView.as_view(), name='pedidos_list'),
    path('pedidos/criar/', api_views.PedidoCreateView.as_view(), name='pedido_create'),
    path('pedidos/<int:pedido_id>/', api_views.PedidoDetailView.as_view(), name='pedido_detail'),
]
