from django.urls import path
from . import api_views

app_name = 'ingredientes_api'

urlpatterns = [
    # Ingredientes
    path('ingredientes/', api_views.IngredientesListView.as_view(), name='ingredientes_list'),
    path('ingredientes/criar/', api_views.IngredienteCreateView.as_view(), name='ingrediente_create'),
    path('ingredientes/<int:ingrediente_id>/', api_views.IngredienteDetailView.as_view(), name='ingrediente_detail'),
]
