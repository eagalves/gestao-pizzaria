from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Ingrediente
from .forms import IngredienteForm


@extend_schema(
    tags=['ingredientes'],
    summary='Listar todos os ingredientes',
    description='Retorna uma lista de todos os ingredientes cadastrados no sistema',
    responses={
        200: {
            'description': 'Lista de ingredientes retornada com sucesso',
            'type': 'object',
            'properties': {
                'ingredientes': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'descricao': {'type': 'string'},
                            'unidade': {'type': 'string'},
                            'preco_unitario': {'type': 'number'},
                            'ativo': {'type': 'boolean'},
                        }
                    }
                }
            }
        }
    }
)
class IngredientesListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os ingredientes"""
        ingredientes = Ingrediente.objects.all()
        data = []
        for ingrediente in ingredientes:
            data.append({
                'id': ingrediente.id,
                'nome': ingrediente.nome,
                'descricao': ingrediente.descricao,
                'unidade': ingrediente.unidade,
                'preco_unitario': float(ingrediente.preco_unitario) if ingrediente.preco_unitario else 0,
                'ativo': ingrediente.ativo,
            })
        
        return Response({'ingredientes': data})


@extend_schema(
    tags=['ingredientes'],
    summary='Cadastrar novo ingrediente',
    description='Cria um novo ingrediente no sistema',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nome': {'type': 'string', 'description': 'Nome do ingrediente'},
                'descricao': {'type': 'string', 'description': 'Descrição do ingrediente'},
                'unidade': {'type': 'string', 'description': 'Unidade de medida'},
                'preco_unitario': {'type': 'number', 'description': 'Preço unitário'},
                'ativo': {'type': 'boolean', 'description': 'Status ativo/inativo'},
            },
            'required': ['nome', 'unidade']
        }
    },
    responses={
        201: {
            'description': 'Ingrediente criado com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'ingrediente': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'descricao': {'type': 'string'},
                        'unidade': {'type': 'string'},
                        'preco_unitario': {'type': 'number'},
                        'ativo': {'type': 'boolean'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
    }
)
class IngredienteCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra um novo ingrediente"""
        form = IngredienteForm(request.data)
        if form.is_valid():
            ingrediente = form.save()
            return Response({
                'message': f'Ingrediente "{ingrediente.nome}" cadastrado com sucesso!',
                'ingrediente': {
                    'id': ingrediente.id,
                    'nome': ingrediente.nome,
                    'descricao': ingrediente.descricao,
                    'unidade': ingrediente.unidade,
                    'preco_unitario': float(ingrediente.preco_unitario) if ingrediente.preco_unitario else 0,
                    'ativo': ingrediente.ativo,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['ingredientes'],
    summary='Obter detalhes de um ingrediente',
    description='Retorna os detalhes de um ingrediente específico',
    parameters=[
        OpenApiParameter(
            name='ingrediente_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID do ingrediente',
            required=True
        ),
    ],
    responses={
        200: {
            'description': 'Detalhes do ingrediente retornados com sucesso',
            'type': 'object',
            'properties': {
                'ingrediente': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'descricao': {'type': 'string'},
                        'unidade': {'type': 'string'},
                        'preco_unitario': {'type': 'number'},
                        'ativo': {'type': 'boolean'},
                    }
                }
            }
        },
        404: {'description': 'Ingrediente não encontrado'},
    }
)
class IngredienteDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, ingrediente_id):
        """Exibe os detalhes de um ingrediente específico"""
        try:
            ingrediente = Ingrediente.objects.get(id=ingrediente_id)
        except Ingrediente.DoesNotExist:
            return Response({
                'error': 'Ingrediente não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'ingrediente': {
                'id': ingrediente.id,
                'nome': ingrediente.nome,
                'descricao': ingrediente.descricao,
                'unidade': ingrediente.unidade,
                'preco_unitario': float(ingrediente.preco_unitario) if ingrediente.preco_unitario else 0,
                'ativo': ingrediente.ativo,
            }
        })
