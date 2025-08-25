from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/super-admin/', views.dashboard_super_admin, name='dashboard_super_admin'),
    path('pizzarias/nova/', views.cadastro_pizzaria, name='cadastro_pizzaria'),
    path('pizzarias/nova/ajax/', views.cadastro_pizzaria_ajax, name='cadastro_pizzaria_ajax'),
    path('pizzarias/', views.lista_pizzarias, name='lista_pizzarias'),
    path('boas-vindas/', views.boas_vindas_pizzaria, name='boas_vindas_pizzaria'),
    path('pizzarias/<int:pizzaria_id>/boas-vindas/', views.visualizar_pizzaria, name='visualizar_pizzaria'),
]