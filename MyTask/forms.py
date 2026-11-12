from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistroForm(UserCreationForm):
    """Formulario de registro con correo electrónico opcional."""

    email = forms.EmailField(
        required=False,
        label='Correo electrónico',
        help_text='Opcional. Se usa para contactarte o recuperar tu cuenta.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['username'].help_text = (
            'Máximo 150 caracteres. Solo letras, números y @/./+/-/_.'
        )
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
