from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Pizzaria, UsuarioPizzaria
from .forms import PizzariaForm


@extend_schema(
    tags=['pizzarias'],
    summary='Listar todas as pizzarias',
    description='Retorna uma lista de todas as pizzarias cadastradas no sistema',
    responses={
        200: {
            'description': 'Lista de pizzarias retornada com sucesso',
            'type': 'object',
            'properties': {
                'pizzarias': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'cnpj': {'type': 'string'},
                            'telefone': {'type': 'string'},
                            'endereco': {'type': 'string'},
                            'ativa': {'type': 'boolean'},
                        }
                    }
                }
            }
        },
        403: {'description': 'Acesso negado - apenas Super Admins'},
    }
)
class PizzariasListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todas as pizzarias (apenas Super Admin)"""
        usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()

        if not usuario_pizzaria:
            return Response({
                'error': 'Usuário sem perfil ativo no sistema'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not usuario_pizzaria.is_super_admin():
            return Response({
                'error': 'Acesso restrito. Apenas Super Administradores podem visualizar a lista de pizzarias.'
            }, status=status.HTTP_403_FORBIDDEN)

        pizzarias = Pizzaria.objects.all()
        data = []
        for pizzaria in pizzarias:
            data.append({
                'id': pizzaria.id,
                'nome': pizzaria.nome,
                'cnpj': pizzaria.cnpj,
                'telefone': pizzaria.telefone,
                'endereco': pizzaria.endereco,
                'ativa': pizzaria.ativa,
            })
        
        return Response({'pizzarias': data})


@extend_schema(
    tags=['pizzarias'],
    summary='Cadastrar nova pizzaria',
    description='Cria uma nova pizzaria no sistema (apenas Super Admin)',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nome': {'type': 'string', 'description': 'Nome da pizzaria'},
                'cnpj': {'type': 'string', 'description': 'CNPJ da pizzaria'},
                'telefone': {'type': 'string', 'description': 'Telefone da pizzaria'},
                'endereco': {'type': 'string', 'description': 'Endereço da pizzaria'},
                'ativa': {'type': 'boolean', 'description': 'Status ativo/inativo'},
            },
            'required': ['nome', 'cnpj', 'telefone', 'endereco']
        }
    },
    responses={
        201: {
            'description': 'Pizzaria criada com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'pizzaria': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'cnpj': {'type': 'string'},
                        'telefone': {'type': 'string'},
                        'endereco': {'type': 'string'},
                        'ativa': {'type': 'boolean'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
        403: {'description': 'Acesso negado - apenas Super Admins'},
    },
    examples=[
        OpenApiExample(
            'Exemplo de criação',
            value={
                'nome': 'Pizzaria Exemplo',
                'cnpj': '12.345.678/0001-90',
                'telefone': '(11) 99999-9999',
                'endereco': 'Rua Exemplo, 123 - Centro',
                'ativa': True
            },
            request_only=True,
            response_only=False,
        ),
    ]
)
class PizzariaCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra uma nova pizzaria (apenas Super Admin)"""
        usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()

        if not usuario_pizzaria:
            return Response({
                'error': 'Usuário sem perfil ativo no sistema'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not usuario_pizzaria.is_super_admin():
            return Response({
                'error': 'Acesso restrito. Apenas Super Administradores podem cadastrar novas pizzarias.'
            }, status=status.HTTP_403_FORBIDDEN)

        form = PizzariaForm(request.data)
        if form.is_valid():
            pizzaria = form.save()
            return Response({
                'message': f'Pizzaria "{pizzaria.nome}" cadastrada com sucesso!',
                'pizzaria': {
                    'id': pizzaria.id,
                    'nome': pizzaria.nome,
                    'cnpj': pizzaria.cnpj,
                    'telefone': pizzaria.telefone,
                    'endereco': pizzaria.endereco,
                    'ativa': pizzaria.ativa,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['pizzarias'],
    summary='Obter detalhes de uma pizzaria',
    description='Retorna os detalhes de uma pizzaria específica',
    parameters=[
        OpenApiParameter(
            name='pizzaria_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID da pizzaria',
            required=True
        ),
    ],
    responses={
        200: {
            'description': 'Detalhes da pizzaria retornados com sucesso',
            'type': 'object',
            'properties': {
                'pizzaria': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'cnpj': {'type': 'string'},
                        'telefone': {'type': 'string'},
                        'endereco': {'type': 'string'},
                        'ativa': {'type': 'boolean'},
                    }
                }
            }
        },
        404: {'description': 'Pizzaria não encontrada'},
        403: {'description': 'Acesso negado'},
    }
)
class PizzariaDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pizzaria_id):
        """Exibe os detalhes de uma pizzaria específica"""
        usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()

        if not usuario_pizzaria:
            return Response({
                'error': 'Usuário sem perfil ativo no sistema'
            }, status=status.HTTP_403_FORBIDDEN)

        # Se for dono de pizzaria, garantir que esteja acessando a própria pizzaria
        if usuario_pizzaria.is_dono_pizzaria() and usuario_pizzaria.pizzaria.id != pizzaria_id:
            return Response({
                'error': 'Acesso restrito. Você só pode visualizar sua própria pizzaria.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            pizzaria = Pizzaria.objects.get(id=pizzaria_id)
        except Pizzaria.DoesNotExist:
            return Response({
                'error': 'Pizzaria não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'pizzaria': {
                'id': pizzaria.id,
                'nome': pizzaria.nome,
                'cnpj': pizzaria.cnpj,
                'telefone': pizzaria.telefone,
                'endereco': pizzaria.endereco,
                'ativa': pizzaria.ativa,
            }
        })


@extend_schema(
    tags=['autenticacao'],
    summary='Dashboard Super Admin',
    description='Retorna estatísticas do dashboard para Super Administradores',
    responses={
        200: {
            'description': 'Estatísticas retornadas com sucesso',
            'type': 'object',
            'properties': {
                'total_pizzarias': {'type': 'integer'},
                'total_usuarios': {'type': 'integer'},
                'total_super_admins': {'type': 'integer'},
                'total_donos': {'type': 'integer'},
            }
        },
        403: {'description': 'Acesso negado - apenas Super Admins'},
    }
)
class DashboardSuperAdminView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retorna estatísticas para o dashboard Super Admin"""
        # Aceitar superusuários Django OU usuários do sistema
        if request.user.is_superuser:
            # Superusuário Django tem acesso total
            pass
        else:
            usuario_pizzaria = UsuarioPizzaria.objects.filter(usuario=request.user, ativo=True).first()
            if not usuario_pizzaria or not usuario_pizzaria.is_super_admin():
                return Response({
                    'error': 'Permissão negada. Apenas Super Admin pode acessar.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Dados para o dashboard
        pizzarias = Pizzaria.objects.all()
        total_pizzarias = pizzarias.count()
        total_usuarios = UsuarioPizzaria.objects.count()
        total_super_admins = UsuarioPizzaria.objects.filter(papel='super_admin').count()
        total_donos = UsuarioPizzaria.objects.filter(papel='dono_pizzaria').count()

        return Response({
            'total_pizzarias': total_pizzarias,
            'total_usuarios': total_usuarios,
            'total_super_admins': total_super_admins,
            'total_donos': total_donos,
        })
