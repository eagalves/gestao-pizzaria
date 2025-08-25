from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import EstoqueIngrediente, Fornecedor, CompraIngrediente
from .forms import EstoqueIngredienteForm, FornecedorForm, CompraIngredienteForm


@extend_schema(
    tags=['estoque'],
    summary='Listar todos os itens do estoque',
    description='Retorna uma lista de todos os itens do estoque',
    responses={
        200: {
            'description': 'Lista de itens do estoque retornada com sucesso',
            'type': 'object',
            'properties': {
                'itens': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'quantidade': {'type': 'number'},
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
class EstoqueListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os itens do estoque"""
        itens = EstoqueIngrediente.objects.all()
        data = []
        for item in itens:
            data.append({
                'id': item.id,
                'nome': item.nome,
                'quantidade': float(item.quantidade) if item.quantidade else 0,
                'unidade': item.unidade,
                'preco_unitario': float(item.preco_unitario) if item.preco_unitario else 0,
                'ativo': item.ativo,
            })
        
        return Response({'itens': data})


@extend_schema(
    tags=['estoque'],
    summary='Cadastrar novo item no estoque',
    description='Cria um novo item no estoque',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nome': {'type': 'string', 'description': 'Nome do item'},
                'quantidade': {'type': 'number', 'description': 'Quantidade em estoque'},
                'unidade': {'type': 'string', 'description': 'Unidade de medida'},
                'preco_unitario': {'type': 'number', 'description': 'Preço unitário'},
                'ativo': {'type': 'boolean', 'description': 'Status ativo/inativo'},
            },
            'required': ['nome', 'quantidade', 'unidade']
        }
    },
    responses={
        201: {
            'description': 'Item criado com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'item': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nome': {'type': 'string'},
                        'quantidade': {'type': 'number'},
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
class EstoqueCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra um novo item no estoque"""
        form = EstoqueIngredienteForm(request.data)
        if form.is_valid():
            item = form.save()
            return Response({
                'message': f'Item "{item.nome}" cadastrado com sucesso!',
                'item': {
                    'id': item.id,
                    'nome': item.nome,
                    'quantidade': float(item.quantidade) if item.quantidade else 0,
                    'unidade': item.unidade,
                    'preco_unitario': float(item.preco_unitario) if item.preco_unitario else 0,
                    'ativo': item.ativo,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['fornecedores'],
    summary='Listar todos os fornecedores',
    description='Retorna uma lista de todos os fornecedores cadastrados',
    responses={
        200: {
            'description': 'Lista de fornecedores retornada com sucesso',
            'type': 'object',
            'properties': {
                'fornecedores': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'cnpj': {'type': 'string'},
                            'telefone': {'type': 'string'},
                            'email': {'type': 'string'},
                            'ativo': {'type': 'boolean'},
                        }
                    }
                }
            }
        }
    }
)
class FornecedoresListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os fornecedores"""
        fornecedores = Fornecedor.objects.all()
        data = []
        for fornecedor in fornecedores:
            data.append({
                'id': fornecedor.id,
                'nome': fornecedor.nome,
                'cnpj': fornecedor.cnpj,
                'telefone': fornecedor.telefone,
                'email': fornecedor.email,
                'ativo': fornecedor.ativo,
            })
        
        return Response({'fornecedores': data})


@extend_schema(
    tags=['compras'],
    summary='Listar todas as compras',
    description='Retorna uma lista de todas as compras realizadas',
    responses={
        200: {
            'description': 'Lista de compras retornada com sucesso',
            'type': 'object',
            'properties': {
                'compras': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'fornecedor': {'type': 'string'},
                            'data_compra': {'type': 'string', 'format': 'date'},
                            'valor_total': {'type': 'number'},
                            'status': {'type': 'string'},
                        }
                    }
                }
            }
        }
    }
)
class ComprasListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todas as compras"""
        compras = CompraIngrediente.objects.all()
        data = []
        for compra in compras:
            data.append({
                'id': compra.id,
                'fornecedor': compra.fornecedor.nome if compra.fornecedor else None,
                'data_compra': compra.data_compra.strftime('%Y-%m-%d') if compra.data_compra else None,
                'valor_total': float(compra.valor_total) if compra.valor_total else 0,
                'status': compra.get_status_display(),
            })
        
        return Response({'compras': data})
