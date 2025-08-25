from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Cliente, EnderecoCliente
from .forms import ClienteForm, EnderecoClienteForm


@extend_schema(
    tags=['clientes'],
    summary='Listar todos os clientes',
    description='Retorna uma lista de todos os clientes cadastrados no sistema',
    responses={
        200: {
            'description': 'Lista de clientes retornada com sucesso',
            'type': 'object',
            'properties': {
                'clientes': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'email': {'type': 'string'},
                            'telefone': {'type': 'string'},
                            'ativo': {'type': 'boolean'},
                        }
                    }
                }
            }
        }
    }
)
class ClientesListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os clientes"""
        clientes = Cliente.objects.all()
        data = []
        for cliente in clientes:
            data.append({
                'id': cliente.id,
                'nome': cliente.nome,
                'email': cliente.email,
                'telefone': cliente.telefone,
                'ativo': cliente.ativo,
            })
        
        return Response({'clientes': data})


@extend_schema(
    tags=['clientes'],
    summary='Cadastrar novo cliente',
    description='Cria um novo cliente no sistema',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nome': {'type': 'string', 'description': 'Nome completo do cliente'},
                'email': {'type': 'string', 'description': 'Email do cliente'},
                'telefone': {'type': 'string', 'description': 'Telefone do cliente'},
                'ativo': {'type': 'boolean', 'description': 'Status ativo/inativo'},
            },
            'required': ['nome', 'email']
        }
    },
    responses={
        201: {
            'description': 'Cliente criado com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'cliente': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'email': {'type': 'string'},
                        'telefone': {'type': 'string'},
                        'ativo': {'type': 'boolean'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
    }
)
class ClienteCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra um novo cliente"""
        form = ClienteForm(request.data)
        if form.is_valid():
            cliente = form.save()
            return Response({
                'message': f'Cliente "{cliente.nome}" cadastrado com sucesso!',
                'cliente': {
                    'id': cliente.id,
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'telefone': cliente.telefone,
                    'ativo': cliente.ativo,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['enderecos'],
    summary='Listar endereços de um cliente',
    description='Retorna uma lista de endereços de um cliente específico',
    parameters=[
        OpenApiParameter(
            name='cliente_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID do cliente',
            required=True
        ),
    ],
    responses={
        200: {
            'description': 'Lista de endereços retornada com sucesso',
            'type': 'object',
            'properties': {
                'enderecos': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'logradouro': {'type': 'string'},
                            'numero': {'type': 'string'},
                            'complemento': {'type': 'string'},
                            'bairro': {'type': 'string'},
                            'cidade': {'type': 'string'},
                            'estado': {'type': 'string'},
                            'cep': {'type': 'string'},
                        }
                    }
                }
            }
        },
        404: {'description': 'Cliente não encontrado'},
    }
)
class ClienteEnderecosView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, cliente_id):
        """Lista endereços de um cliente específico"""
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'error': 'Cliente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        enderecos = EnderecoCliente.objects.filter(cliente=cliente)
        data = []
        for endereco in enderecos:
            data.append({
                'id': endereco.id,
                'logradouro': endereco.logradouro,
                'numero': endereco.numero,
                'complemento': endereco.complemento,
                'bairro': endereco.bairro,
                'cidade': endereco.cidade,
                'estado': endereco.estado,
                'cep': endereco.cep,
            })
        
        return Response({'enderecos': data})
