from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from MyTask import views as mytask_views

urlpatterns = [
    path(
        '',
        RedirectView.as_view(pattern_name='mytask:index', permanent=False),
        name='inicio',
    ),
    path('admin/', admin.site.urls),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', mytask_views.registro, name='registro'),
    path('myTask/', include('MyTask.urls')),
]
