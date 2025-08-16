from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_pedidos, name='lista_pedidos'),
    path('<int:pedido_id>/alterar-status/', views.alterar_status_pedido, name='alterar_status_pedido'),
    path('<int:pedido_id>/detalhes/', views.detalhes_pedido, name='detalhes_pedido'),
    path('<int:pedido_id>/editar/', views.editar_pedido, name='editar_pedido'),
    path('<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
]
