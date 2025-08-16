from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_pedidos, name='lista_pedidos'),
    path('<int:pedido_id>/alterar-status/', views.alterar_status_pedido, name='alterar_status_pedido'),
]
