from django.db import models
from autenticacao.models import Pizzaria

class Ingrediente(models.Model):
    """
    Representa um ingrediente que pertence a uma pizzaria específica.
    """
    pizzaria = models.ForeignKey(Pizzaria, on_delete=models.CASCADE, related_name="ingredientes")
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, help_text="Descrição opcional do ingrediente.")
    vegetariano = models.BooleanField(default=False)
    vegano = models.BooleanField(default=False)
    contem_gluten = models.BooleanField(default=False)
    contem_lactose = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"
        # Garante que não haja ingredientes com o mesmo nome para a mesma pizzaria
        unique_together = ('pizzaria', 'nome')
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.pizzaria.nome})"
