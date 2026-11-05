from django.db import models


class Tarea(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo


class Registro(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='registros')
    detalle = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.fecha:%d/%m/%Y} - {self.detalle}'
