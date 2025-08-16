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
]
