from django.urls import path

from . import views

app_name = 'mytask'
urlpatterns = [
    path('', views.index, name='index'),
    path('nueva/', views.agregar_tarea, name='agregar_tarea'),
    path('tarea/<int:tarea_id>/', views.detalle, name='detalle'),
    path('tarea/<int:tarea_id>/editar/', views.editar_tarea, name='editar_tarea'),
    path('tarea/<int:tarea_id>/eliminar/', views.eliminar_tarea, name='eliminar_tarea'),
    path('tarea/<int:tarea_id>/registro/', views.agregar_registro, name='agregar_registro'),
    path('tarea/<int:tarea_id>/completar/', views.completar_tarea, name='completar_tarea'),
]
