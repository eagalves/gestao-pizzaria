from django.urls import path
from . import views

urlpatterns = [
    # ==================== ROTAS DE CLIENTES ====================
    path("", views.lista_clientes, name="lista_clientes"),
    path("<int:cliente_id>/detalhes/", views.detalhes_cliente, name="detalhes_cliente"),
    path("<int:cliente_id>/editar/", views.editar_cliente, name="editar_cliente"),
    path("<int:cliente_id>/excluir/", views.excluir_cliente, name="excluir_cliente"),
    
    # ==================== ROTAS DE ENDEREÇOS ====================
    path("<int:cliente_id>/endereco/adicionar/", views.adicionar_endereco, name="adicionar_endereco"),
    path("endereco/<int:endereco_id>/editar/", views.editar_endereco, name="editar_endereco"),
    path("endereco/<int:endereco_id>/excluir/", views.excluir_endereco, name="excluir_endereco"),
    path("endereco/<int:endereco_id>/principal/", views.definir_endereco_principal, name="definir_endereco_principal"),
    
    # ==================== API ====================
    path("buscar/", views.buscar_clientes, name="buscar_clientes"),
]
