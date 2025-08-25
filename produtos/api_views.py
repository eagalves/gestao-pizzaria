from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Produto, CategoriaProduto, ProdutoIngrediente
from .forms import ProdutoForm, CategoriaForm


@extend_schema(
    tags=['produtos'],
    summary='Listar todos os produtos',
    description='Retorna uma lista de todos os produtos cadastrados no sistema',
    responses={
        200: {
            'description': 'Lista de produtos retornada com sucesso',
            'type': 'object',
            'properties': {
                'produtos': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'categoria': {'type': 'string'},
                            'preco_venda': {'type': 'number'},
                            'ativo': {'type': 'boolean'},
                        }
                    }
                }
            }
        }
    }
)
class ProdutosListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os produtos"""
        produtos = Produto.objects.all()
        data = []
        for produto in produtos:
            data.append({
                'id': produto.id,
                'nome': produto.nome,
                'categoria': produto.categoria.nome if produto.categoria else None,
                'preco_venda': float(produto.preco_venda) if produto.preco_venda else None,
                'ativo': produto.ativo,
            })
        
        return Response({'produtos': data})


@extend_schema(
    tags=['produtos'],
    summary='Cadastrar novo produto',
    description='Cria um novo produto no sistema',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nome': {'type': 'string', 'description': 'Nome do produto'},
                'categoria': {'type': 'integer', 'description': 'ID da categoria'},
                'preco_venda': {'type': 'number', 'description': 'Preço de venda'},
                'ativo': {'type': 'boolean', 'description': 'Status ativo/inativo'},
            },
            'required': ['nome', 'categoria']
        }
    },
    responses={
        201: {
            'description': 'Produto criado com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'produto': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'categoria': {'type': 'string'},
                        'preco_venda': {'type': 'number'},
                        'ativo': {'type': 'boolean'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
    }
)
class ProdutoCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra um novo produto"""
        form = ProdutoForm(request.data)
        if form.is_valid():
            produto = form.save()
            return Response({
                'message': f'Produto "{produto.nome}" cadastrado com sucesso!',
                'produto': {
                    'id': produto.id,
                    'nome': produto.nome,
                    'categoria': produto.categoria.nome if produto.categoria else None,
                    'preco_venda': float(produto.preco_venda) if produto.preco_venda else None,
                    'ativo': produto.ativo,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['categorias'],
    summary='Listar todas as categorias',
    description='Retorna uma lista de todas as categorias de produtos',
    responses={
        200: {
            'description': 'Lista de categorias retornada com sucesso',
            'type': 'object',
            'properties': {
                'categorias': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'descricao': {'type': 'string'},
                            'ativa': {'type': 'boolean'},
                        }
                    }
                }
            }
        }
    }
)
class CategoriasListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todas as categorias"""
        categorias = CategoriaProduto.objects.all()
        data = []
        for categoria in categorias:
            data.append({
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao,
                'ativa': categoria.ativa,
            })
        
        return Response({'categorias': data})


@extend_schema(
    tags=['categorias'],
    summary='Cadastrar nova categoria',
    description='Cria uma nova categoria de produtos',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nome': {'type': 'string', 'description': 'Nome da categoria'},
                'descricao': {'type': 'string', 'description': 'Descrição da categoria'},
                'ativa': {'type': 'boolean', 'description': 'Status ativo/inativo'},
            },
            'required': ['nome']
        }
    },
    responses={
        201: {
            'description': 'Categoria criada com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'categoria': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'descricao': {'type': 'string'},
                        'ativa': {'type': 'boolean'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
    }
)
class CategoriaCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra uma nova categoria"""
        form = CategoriaForm(request.data)
        if form.is_valid():
            categoria = form.save()
            return Response({
                'message': f'Categoria "{categoria.nome}" cadastrada com sucesso!',
                'categoria': {
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'descricao': categoria.descricao,
                    'ativa': categoria.ativa,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)
