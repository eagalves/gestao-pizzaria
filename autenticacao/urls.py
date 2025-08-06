from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/super-admin/', views.dashboard_super_admin, name='dashboard_super_admin'),
    path('pizzarias/nova/', views.cadastro_pizzaria, name='cadastro_pizzaria'),
    path('pizzarias/', views.lista_pizzarias, name='lista_pizzarias'),
]