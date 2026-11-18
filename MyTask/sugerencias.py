"""Cliente HTTP de Django hacia el microservicio Node.js de sugerencias."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

MENSAJE_GENERICO = 'El servicio de sugerencias no está disponible en este momento. Intenta de nuevo más tarde.'


class SugerenciasNoDisponibles(Exception):
    """El servicio de sugerencias falló; el mensaje está pensado para mostrarse al usuario."""


def _mensaje_del_servicio(error):
    """Devuelve el mensaje de un 502 del microservicio (ya viene en español)."""
    try:
        mensaje = json.loads(error.read().decode('utf-8')).get('error')
    except (ValueError, AttributeError, OSError):
        return MENSAJE_GENERICO
    return mensaje if isinstance(mensaje, str) and mensaje else MENSAJE_GENERICO


def pedir_sugerencias(tarea):
    """Pide al microservicio las subtareas sugeridas para una tarea."""
    url = settings.NODE_SERVICE_URL.rstrip('/') + '/api/sugerencias'
    peticion = Request(
        url,
        data=json.dumps(
            {'titulo': tarea.titulo, 'descripcion': tarea.descripcion}
        ).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': settings.INTERNAL_API_KEY,
        },
        method='POST',
    )
    try:
        with urlopen(peticion, timeout=settings.SUGERENCIAS_TIMEOUT) as respuesta:
            cuerpo = respuesta.read()
    except HTTPError as error:
        # Solo el 502 trae un mensaje apto para el usuario; el resto no se expone.
        mensaje = _mensaje_del_servicio(error) if error.code == 502 else MENSAJE_GENERICO
        raise SugerenciasNoDisponibles(mensaje) from error
    except TimeoutError as error:
        raise SugerenciasNoDisponibles(
            'El servicio de sugerencias tardó demasiado en responder. Intenta de nuevo.'
        ) from error
    except (URLError, OSError) as error:
        raise SugerenciasNoDisponibles(
            'No se pudo conectar con el servicio de sugerencias. Intenta de nuevo más tarde.'
        ) from error

    try:
        subtareas = json.loads(cuerpo.decode('utf-8'))['subtareas']
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise SugerenciasNoDisponibles(MENSAJE_GENERICO) from error
    if not isinstance(subtareas, list) or not all(isinstance(s, str) for s in subtareas):
        raise SugerenciasNoDisponibles(MENSAJE_GENERICO)
    return subtareas
