from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Herramienta


class HerramientaForm(forms.ModelForm):
    class Meta:
        model = Herramienta
        fields = ["nombre", "tipo", "stock"]


class CrearUsuarioForm(UserCreationForm):
    ROL_CHOICES = (
        ('PANOLERO', 'Pañolero'),
        ('DOCENTE', 'Docente'),
    )

    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo institucional')
    rol = forms.ChoiceField(label='Tipo de usuario', choices=ROL_CHOICES)

    class Meta:
        model = User
        fields = [
            'username',      # ej: m_vargas
            'first_name',    # Mauricio
            'last_name',     # Vargas
            'email',
            'rol',           # Pañolero o Docente
            'password1',
            'password2',
        ]
