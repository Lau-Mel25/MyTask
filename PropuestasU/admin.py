# Register your models here.
from django.contrib import admin

# Register your models here.
from .models import Propuesta,OpcionVoto

admin.site.register(Propuesta)
admin.site.register(OpcionVoto)