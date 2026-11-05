from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.http import HttpResponseRedirect
from django.urls import reverse

# Create your views here.
from .models import Propuesta,OpcionVoto


def index(request):
    propuestas = Propuesta.objects.all().order_by('-fecha_creacion')
    contexto = {
        'propuestas': propuestas,
    }
    return render(request, 'PropuestasU/index.html', contexto)


def detalle(request, propuesta_id):
    propuesta = get_object_or_404(Propuesta, pk=propuesta_id)
    opciones = propuesta.votosxpropuesta.all()
    contexto = {
        'propuesta': propuesta,
        'opciones': opciones,
    }
    return render(request, "PropuestasU/detalle.html", contexto)


def votar(request, propuesta_id):
    propuesta = get_object_or_404(Propuesta, pk=propuesta_id)
    try:
        opcion_elegida = propuesta.votosxpropuesta.get(pk=request.POST["opcion"])
    except (KeyError, OpcionVoto.DoesNotExist):
        # Vuelve a mostrar el formulario de votación.
        return render(
            request,
            "PropuestasU/detalle.html",
            {
                "propuesta": propuesta,
                "error_message": "No seleccionaste ninguna opción.",
            },
        )
    else:
        opcion_elegida.votos = F("votos") + 1
        opcion_elegida.save()
        return HttpResponseRedirect(
            reverse("propuestas:resultados", args=(propuesta.id,))
        )

def resultados(request, propuesta_id):
    propuesta = get_object_or_404(Propuesta, pk=propuesta_id)
    return render(request, 'PropuestasU/resultados.html', {'propuesta': propuesta})