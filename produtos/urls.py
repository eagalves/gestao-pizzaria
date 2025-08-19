from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_produtos, name="lista_produtos"),
    # rota para editar produto
    path("<int:produto_id>/editar/", views.editar_produto, name="editar_produto"),
    # rota para obter ingredientes do produto (AJAX)
    path("<int:produto_id>/ingredientes/", views.ingredientes_produto, name="ingredientes_produto"),
    # rota para excluir produto
    path("<int:produto_id>/excluir/", views.excluir_produto, name="excluir_produto"),
    # rota para gerenciar preços
    path("<int:produto_id>/precos/", views.gerenciar_precos, name="gerenciar_precos"),
    
    # ==================== ROTAS DE CATEGORIAS ====================
    path("categorias/", views.lista_categorias, name="lista_categorias"),
    path("categorias/<int:categoria_id>/editar/", views.editar_categoria, name="editar_categoria"),
    path("categorias/<int:categoria_id>/excluir/", views.excluir_categoria, name="excluir_categoria"),
    path("categorias/reordenar/", views.reordenar_categorias, name="reordenar_categorias"),
]
