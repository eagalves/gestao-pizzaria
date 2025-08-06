from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_ingredientes, name="lista_ingredientes"),
]