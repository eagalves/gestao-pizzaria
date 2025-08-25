from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import DespesaOperacional, TipoDespesa, MetaVenda
from .forms import DespesaOperacionalForm, TipoDespesaForm


@extend_schema(
    tags=['financeiro'],
    summary='Listar todas as despesas',
    description='Retorna uma lista de todas as despesas cadastradas',
    responses={
        200: {
            'description': 'Lista de despesas retornada com sucesso',
            'type': 'object',
            'properties': {
                'despesas': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'descricao': {'type': 'string'},
                            'valor': {'type': 'number'},
                            'data_vencimento': {'type': 'string', 'format': 'date'},
                            'status': {'type': 'string'},
                            'tipo': {'type': 'string'},
                        }
                    }
                }
            }
        }
    }
)
class DespesasListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todas as despesas"""
        despesas = DespesaOperacional.objects.all()
        data = []
        for despesa in despesas:
            data.append({
                'id': despesa.id,
                'descricao': despesa.descricao,
                'valor': float(despesa.valor) if despesa.valor else 0,
                'data_vencimento': despesa.data_vencimento.strftime('%Y-%m-%d') if despesa.data_vencimento else None,
                'status': despesa.get_status_display(),
                'tipo': despesa.tipo.nome if despesa.tipo else None,
            })
        
        return Response({'despesas': data})


@extend_schema(
    tags=['financeiro'],
    summary='Cadastrar nova despesa',
    description='Cria uma nova despesa no sistema',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'descricao': {'type': 'string', 'description': 'Descrição da despesa'},
                'valor': {'type': 'number', 'description': 'Valor da despesa'},
                'data_vencimento': {'type': 'string', 'format': 'date', 'description': 'Data de vencimento'},
                'tipo': {'type': 'integer', 'description': 'ID do tipo de despesa'},
                'recorrente': {'type': 'boolean', 'description': 'Se é uma despesa recorrente'},
            },
            'required': ['descricao', 'valor', 'tipo']
        }
    },
    responses={
        201: {
            'description': 'Despesa criada com sucesso',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'despesa': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'descricao': {'type': 'string'},
                        'valor': {'type': 'number'},
                        'data_vencimento': {'type': 'string', 'format': 'date'},
                        'tipo': {'type': 'string'},
                        'recorrente': {'type': 'boolean'},
                    }
                }
            }
        },
        400: {'description': 'Dados inválidos'},
    }
)
class DespesaCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cadastra uma nova despesa"""
        form = DespesaOperacionalForm(request.data)
        if form.is_valid():
            despesa = form.save()
            return Response({
                'message': f'Despesa "{despesa.descricao}" cadastrada com sucesso!',
                'despesa': {
                    'id': despesa.id,
                    'descricao': despesa.descricao,
                    'valor': float(despesa.valor) if despesa.valor else 0,
                    'data_vencimento': despesa.data_vencimento.strftime('%Y-%m-%d') if despesa.data_vencimento else None,
                    'tipo': despesa.tipo.nome if despesa.tipo else None,
                    'recorrente': despesa.recorrente,
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Dados inválidos',
                'details': form.errors
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['financeiro'],
    summary='Listar tipos de despesa',
    description='Retorna uma lista de todos os tipos de despesa cadastrados',
    responses={
        200: {
            'description': 'Lista de tipos de despesa retornada com sucesso',
            'type': 'object',
            'properties': {
                'tipos': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'nome': {'type': 'string'},
                            'descricao': {'type': 'string'},
                            'ativo': {'type': 'boolean'},
                        }
                    }
                }
            }
        }
    }
)
class TiposDespesaListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os tipos de despesa"""
        tipos = TipoDespesa.objects.all()
        data = []
        for tipo in tipos:
            data.append({
                'id': tipo.id,
                'nome': tipo.nome,
                'descricao': tipo.descricao,
                'ativo': tipo.ativo,
            })
        
        return Response({'tipos': data})


@extend_schema(
    tags=['financeiro'],
    summary='Listar metas de venda',
    description='Retorna uma lista de todas as metas de venda cadastradas',
    responses={
        200: {
            'description': 'Lista de metas de venda retornada com sucesso',
            'type': 'object',
            'properties': {
                'metas': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'mes': {'type': 'string'},
                            'ano': {'type': 'integer'},
                            'valor_meta': {'type': 'number'},
                            'valor_realizado': {'type': 'number'},
                            'percentual': {'type': 'number'},
                        }
                    }
                }
            }
        }
    }
)
class MetasVendaListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todas as metas de venda"""
        metas = MetaVenda.objects.all()
        data = []
        for meta in metas:
            data.append({
                'id': meta.id,
                'mes': meta.get_mes_display(),
                'ano': meta.ano,
                'valor_meta': float(meta.valor_meta) if meta.valor_meta else 0,
                'valor_realizado': float(meta.valor_realizado) if meta.valor_realizado else 0,
                'percentual': float(meta.percentual) if meta.percentual else 0,
            })
        
        return Response({'metas': data})
