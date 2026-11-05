from django.urls import path
from . import views


app_name = 'propuestas'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:propuesta_id>/', views.detalle, name='detalle'),
    path('<int:propuesta_id>/votar/', views.votar, name='votar'),
    path('<int:propuesta_id>/resultados/', views.resultados, name='resultados'),
]