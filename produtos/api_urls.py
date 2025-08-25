from django.urls import path
from . import api_views

app_name = 'produtos_api'

urlpatterns = [
    # Produtos
    path('produtos/', api_views.ProdutosListView.as_view(), name='produtos_list'),
    path('produtos/criar/', api_views.ProdutoCreateView.as_view(), name='produto_create'),
    
    # Categorias
    path('categorias/', api_views.CategoriasListView.as_view(), name='categorias_list'),
    path('categorias/criar/', api_views.CategoriaCreateView.as_view(), name='categoria_create'),
]
