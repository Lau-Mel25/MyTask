from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Perfil, Registro, Tarea


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name = 'perfil y rol'
    verbose_name_plural = 'perfil y rol'
    fk_name = 'usuario'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'get_rol', 'is_staff', 'is_active')
    list_select_related = ('perfil',)

    @admin.display(description='Rol')
    def get_rol(self, obj):
        perfil = getattr(obj, 'perfil', None)
        return perfil.get_rol_display() if perfil else '—'

    def save_formset(self, request, form, formset, change):
        """Guarda el perfil sin duplicarlo cuando se crea un usuario nuevo."""
        instancias = formset.save(commit=False)
        for instancia in instancias:
            if isinstance(instancia, Perfil):
                perfil, _ = Perfil.objects.get_or_create(usuario=form.instance)
                perfil.rol = instancia.rol
                perfil.save()
            else:
                instancia.save()
        formset.save_m2m()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'propietario', 'completada', 'fecha_creacion')
    list_filter = ('completada', 'propietario')
    list_editable = ('completada',)
    search_fields = ('titulo', 'descripcion', 'propietario__username')
    autocomplete_fields = ('propietario',)
    date_hierarchy = 'fecha_creacion'


@admin.register(Registro)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('detalle', 'tarea', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('detalle', 'tarea__titulo')
    autocomplete_fields = ('tarea',)
