from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def es_administrador(user):
    """Indica si el usuario tiene el rol de administrador."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil', None)
    return bool(perfil and perfil.es_administrador)


def solo_administradores(vista):
    """Restringe una vista a los usuarios con rol de administrador."""

    @login_required
    @wraps(vista)
    def _vista_protegida(request, *args, **kwargs):
        if not es_administrador(request.user):
            raise PermissionDenied
        return vista(request, *args, **kwargs)

    return _vista_protegida
