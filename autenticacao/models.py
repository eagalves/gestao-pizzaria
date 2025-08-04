from django.db import models

# Create your models here.

class Pizzaria(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=14, unique=True)
    endereco = models.TextField()
    telefone = models.CharField(max_length=15)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pizzaria"
        verbose_name_plural = "Pizzarias"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    # Futuro: configurações específicas da pizzaria
    # cor_tema, logo, configurações_delivery, etc.
