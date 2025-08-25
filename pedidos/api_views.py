from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Pedido, ItemPedido
from .forms import PedidoForm, ItemPedidoForm


@extend_schema(
    tags=['pedidos'],
    summary='Listar todos os pedidos',
    description='Retorna uma lista de todos os pedidos cadastrados no sistema',
    responses={
        200: {
            'description': 'Lista de pedidos retornada com sucesso',
            'type': 'object',
            'properties': {
                'pedidos': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'cliente': {'type': 'string'},
                            'data_pedido': {'type': 'string', 'format': 'date'},
                            'valor_total': {'type': 'number'},
                            'status': {'type': 'string'},
                        }
                    }
                }
            }
        }
    }
)
class PedidosListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os pedidos"""
        pedidos = Pedido.objects.all()
        data = []
        for pedido in pedidos:
            data.append({
                'id': pedido.id,
                'cliente': pedido.get_cliente_nome(),
                'data_pedido': pedido.data_criacao.strftime('%Y-%m-%d') if pedido.data_criacao else None,
                'valor_total': float(pedido.total) if pedido.total else 0,
                'status': pedido.get_status_display(),
            })
        
        return Response({'pedidos': data})


@extend_schema(
    tags=['pedidos'],
    summary='Cadastrar novo pedido',
    description='Cria um novo pedido no sistema',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'cliente': {'type': 'integer', 'description': 'ID do cliente (opcional)'},
                'cliente_nome': {'type': 'string', 'description': 'Nome do cliente (para pedidos sem cadastro)'},
                'cliente_telefone': {'type': 'string', 'description': 'Telefone do cliente (para pedidos sem cadastro)'},
                'observacoes': {'type': 'string', 'description': 'Observações do pedido'},
                'forma_pagamento': {'type': 'string', 'description': 'Forma de pagamento'},
                'status': {'type': 'string', 'description': 'Status do pedido'},
            },
            'required': ['forma_pagamento']
        }
    },
    responses={
        201: {
            'description': 'Pedido criado com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'pedido': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'cliente': {'type': 'string'},
                        'data_pedido': {'type': 'string', 'format': 'date'},
                        'valor_total': {'type': 'number'},
                        'status': {'type': 'string'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
    }
)
class PedidoCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra um novo pedido"""
        form = PedidoForm(request.data)
        if form.is_valid():
            pedido = form.save()
            return Response({
                'message': f'Pedido #{pedido.id} criado com sucesso!',
                'pedido': {
                    'id': pedido.id,
                    'cliente': pedido.get_cliente_nome(),
                    'data_pedido': pedido.data_criacao.strftime('%Y-%m-%d') if pedido.data_criacao else None,
                    'valor_total': float(pedido.total) if pedido.total else 0,
                    'status': pedido.get_status_display(),
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['pedidos'],
    summary='Obter detalhes de um pedido',
    description='Retorna os detalhes de um pedido específico',
    parameters=[
        OpenApiParameter(
            name='pedido_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID do pedido',
            required=True
        ),
    ],
    responses={
        200: {
            'description': 'Detalhes do pedido retornados com sucesso',
            'type': 'object',
            'properties': {
                'pedido': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'cliente': {'type': 'string'},
                        'data_pedido': {'type': 'string', 'format': 'date'},
                        'valor_total': {'type': 'number'},
                        'status': {'type': 'string'},
                        'observacoes': {'type': 'string'},
                        'itens': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'integer'},
                                    'produto': {'type': 'string'},
                                    'quantidade': {'type': 'number'},
                                    'preco_unitario': {'type': 'number'},
                                    'subtotal': {'type': 'number'},
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {'description': 'Pedido não encontrado'},
    }
)
class PedidoDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pedido_id):
        """Exibe os detalhes de um pedido específico"""
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response({
                'error': 'Pedido não encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Buscar itens do pedido
        itens = ItemPedido.objects.filter(pedido=pedido)
        itens_data = []
        for item in itens:
            itens_data.append({
                'id': item.id,
                'produto': item.produto.nome if item.produto else None,
                'quantidade': float(item.quantidade) if item.quantidade else 0,
                'preco_unitario': float(item.valor_unitario) if item.valor_unitario else 0,
                'subtotal': float(item.subtotal) if item.subtotal else 0,
            })

        return Response({
            'pedido': {
                'id': pedido.id,
                'cliente': pedido.get_cliente_nome(),
                'data_pedido': pedido.data_criacao.strftime('%Y-%m-%d') if pedido.data_criacao else None,
                'valor_total': float(pedido.total) if pedido.total else 0,
                'status': pedido.get_status_display(),
                'observacoes': pedido.observacoes,
                'itens': itens_data
            }
        })
