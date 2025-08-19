# Generated manually

from django.db import migrations


def converter_unidades_antigas(apps, schema_editor):
    """Converte unidades antigas para o novo sistema simplificado."""
    ProdutoIngrediente = apps.get_model('produtos', 'ProdutoIngrediente')
    
    # Mapeamento de unidades antigas para novas
    conversoes = {
        'ml': 'g',      # mililitros → gramas
        'l': 'kg',      # litros → quilos
        'fatia': 'un',  # fatia → unidade
        'pitada': 'g',  # pitada → gramas
    }
    
    for produto_ingrediente in ProdutoIngrediente.objects.all():
        unidade_antiga = produto_ingrediente.unidade
        
        if unidade_antiga in conversoes:
            nova_unidade = conversoes[unidade_antiga]
            produto_ingrediente.unidade = nova_unidade
            produto_ingrediente.save()
            print(f"Convertido: {unidade_antiga} → {nova_unidade} para {produto_ingrediente.ingrediente.nome}")


def reverter_conversao(apps, schema_editor):
    """Não é possível reverter automaticamente."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0004_simplificar_unidades'),
    ]

    operations = [
        migrations.RunPython(converter_unidades_antigas, reverter_conversao),
    ]
