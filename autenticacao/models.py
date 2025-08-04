from django.db import models
from django.contrib.auth.models import User

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


class UsuarioPizzaria(models.Model):
    PAPEIS = [
        ('super_admin', 'Super Admin'),           # Você (cadastra pizzarias)
        ('dono_pizzaria', 'Dono da Pizzaria'),    # Dono - só vê boas-vindas
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuarios_pizzaria')
    pizzaria = models.ForeignKey(Pizzaria, on_delete=models.CASCADE, null=True, blank=True, related_name='usuarios_pizzaria')  # Super admin não tem pizzaria específica
    papel = models.CharField(max_length=20, choices=PAPEIS)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Usuário Pizzaria"
        verbose_name_plural = "Usuários Pizzaria"
        unique_together = ['usuario', 'pizzaria']  # Um usuário pode ter apenas um papel por pizzaria
        ordering = ['usuario__username']
    
    def is_super_admin(self):
        """Verifica se é super admin"""
        return self.papel == 'super_admin'
    
    def is_dono_pizzaria(self):
        """Verifica se é dono de pizzaria"""
        return self.papel == 'dono_pizzaria'
    
    def __str__(self):
        if self.pizzaria:
            return f"{self.usuario.username} - {self.get_papel_display()} - {self.pizzaria.nome}"
        else:
            return f"{self.usuario.username} - {self.get_papel_display()}"
