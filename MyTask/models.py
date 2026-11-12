from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Tarea(models.Model):
    propietario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tareas',
        verbose_name='propietario',
    )
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'tarea'
        verbose_name_plural = 'tareas'

    def __str__(self):
        return self.titulo


class Registro(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='registros')
    detalle = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'registro'
        verbose_name_plural = 'registros'

    def __str__(self):
        return f'{self.fecha:%d/%m/%Y} - {self.detalle}'


class Perfil(models.Model):
    """Datos adicionales del usuario: su rol dentro de la aplicación."""

    class Rol(models.TextChoices):
        USUARIO = 'usuario', 'Usuario'
        ADMINISTRADOR = 'administrador', 'Administrador'

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.USUARIO,
    )

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfiles'

    def __str__(self):
        return f'{self.usuario.username} ({self.get_rol_display()})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._sincronizar_acceso_admin()

    def _sincronizar_acceso_admin(self):
        """Mantiene el acceso a Django Admin alineado con el rol."""
        usuario = self.usuario
        if usuario.is_superuser:
            return
        debe_ser_staff = self.rol == self.Rol.ADMINISTRADOR
        if usuario.is_staff != debe_ser_staff:
            usuario.is_staff = debe_ser_staff
            usuario.save(update_fields=['is_staff'])

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR or self.usuario.is_superuser


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    """Crea automáticamente el perfil cuando se registra un usuario."""
    if created:
        rol = Perfil.Rol.ADMINISTRADOR if instance.is_superuser else Perfil.Rol.USUARIO
        Perfil.objects.get_or_create(usuario=instance, defaults={'rol': rol})
