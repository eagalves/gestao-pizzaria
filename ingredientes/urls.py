from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_ingredientes, name="lista_ingredientes"),
    # nova rota para editar ingrediente
    path("<int:ingrediente_id>/editar/", views.editar_ingrediente, name="editar_ingrediente"),
    # nova rota para excluir ingrediente
    path("<int:ingrediente_id>/excluir/", views.excluir_ingrediente, name="excluir_ingrediente"),
]