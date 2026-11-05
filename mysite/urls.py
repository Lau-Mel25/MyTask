from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('myTask/', include('MyTask.urls')),
    path('propuestas/', include('PropuestasU.urls')),
]
