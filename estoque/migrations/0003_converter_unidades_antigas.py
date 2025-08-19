# Generated manually

from django.db import migrations


def converter_unidades_antigas(apps, schema_editor):
    """Converte unidades antigas para o novo sistema simplificado."""
    EstoqueIngrediente = apps.get_model('estoque', 'EstoqueIngrediente')
    
    # Mapeamento de unidades antigas para novas
    conversoes = {
        'ml': 'g',      # mililitros → gramas
        'l': 'kg',      # litros → quilos
        'fatia': 'un',  # fatia → unidade
        'pitada': 'g',  # pitada → gramas
    }
    
    for estoque in EstoqueIngrediente.objects.all():
        unidade_antiga = estoque.unidade_medida
        
        if unidade_antiga in conversoes:
            nova_unidade = conversoes[unidade_antiga]
            estoque.unidade_medida = nova_unidade
            estoque.save()
            print(f"Convertido estoque: {unidade_antiga} → {nova_unidade} para {estoque.ingrediente.nome}")


def reverter_conversao(apps, schema_editor):
    """Não é possível reverter automaticamente."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0002_simplificar_unidades'),
    ]

    operations = [
        migrations.RunPython(converter_unidades_antigas, reverter_conversao),
    ]
