from django.urls import path
from . import api_views

app_name = 'autenticacao_api'

urlpatterns = [
    # Pizzarias
    path('pizzarias/', api_views.PizzariasListView.as_view(), name='pizzarias_list'),
    path('pizzarias/criar/', api_views.PizzariaCreateView.as_view(), name='pizzaria_create'),
    path('pizzarias/<int:pizzaria_id>/', api_views.PizzariaDetailView.as_view(), name='pizzaria_detail'),
    
    # Dashboard
    path('dashboard/super-admin/', api_views.DashboardSuperAdminView.as_view(), name='dashboard_super_admin'),
]
