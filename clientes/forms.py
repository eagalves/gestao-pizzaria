from django import forms
from .models import Cliente, EnderecoCliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'email', 'data_nascimento', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do cliente'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'cliente@email.com'
            }),
            'data_nascimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre o cliente (opcional)'
            })
        }
        labels = {
            'nome': 'Nome Completo',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'data_nascimento': 'Data de Nascimento',
            'observacoes': 'Observações'
        }

    def __init__(self, *args, **kwargs):
        self.pizzaria = kwargs.pop('pizzaria', None)
        super().__init__(*args, **kwargs)

    def clean_telefone(self):
        telefone = self.cleaned_data['telefone']
        if self.pizzaria:
            # Verifica se já existe outro cliente com o mesmo telefone na pizzaria
            qs = Cliente.objects.filter(pizzaria=self.pizzaria, telefone=telefone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Já existe um cliente com este telefone.')
        return telefone


class EnderecoClienteForm(forms.ModelForm):
    class Meta:
        model = EnderecoCliente
        fields = ['nome', 'cep', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'referencia']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Casa, Trabalho'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345-678',
                'maxlength': '10'
            }),
            'rua': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da rua'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apto, Bloco, etc. (opcional)'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da cidade'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', '---'),
                ('AC', 'Acre'),
                ('AL', 'Alagoas'),
                ('AP', 'Amapá'),
                ('AM', 'Amazonas'),
                ('BA', 'Bahia'),
                ('CE', 'Ceará'),
                ('DF', 'Distrito Federal'),
                ('ES', 'Espírito Santo'),
                ('GO', 'Goiás'),
                ('MA', 'Maranhão'),
                ('MT', 'Mato Grosso'),
                ('MS', 'Mato Grosso do Sul'),
                ('MG', 'Minas Gerais'),
                ('PA', 'Pará'),
                ('PB', 'Paraíba'),
                ('PR', 'Paraná'),
                ('PE', 'Pernambuco'),
                ('PI', 'Piauí'),
                ('RJ', 'Rio de Janeiro'),
                ('RN', 'Rio Grande do Norte'),
                ('RS', 'Rio Grande do Sul'),
                ('RO', 'Rondônia'),
                ('RR', 'Roraima'),
                ('SC', 'Santa Catarina'),
                ('SP', 'São Paulo'),
                ('SE', 'Sergipe'),
                ('TO', 'Tocantins'),
            ]),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ponto de referência (opcional)'
            })
        }
        labels = {
            'nome': 'Nome do Endereço',
            'cep': 'CEP',
            'rua': 'Rua/Avenida',
            'numero': 'Número',
            'complemento': 'Complemento',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'Estado',
            'referencia': 'Referência'
        }
