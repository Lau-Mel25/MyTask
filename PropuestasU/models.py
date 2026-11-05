from django.db import models

# Create your models here.

class Propuesta(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class OpcionVoto(models.Model):
    propuesta = models.ForeignKey(Propuesta, on_delete=models.CASCADE, related_name='votosxpropuesta')
    texto = models.CharField(max_length=100)
    votos = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.propuesta.titulo} - {self.texto}'