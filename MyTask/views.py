from django.shortcuts import render, redirect, get_object_or_404

from .models import Tarea


def index(request):
    tareas_pendientes = Tarea.objects.filter(completada=False).order_by('-fecha_creacion')
    tareas_completadas = Tarea.objects.filter(completada=True).order_by('-fecha_creacion')
    contexto = {
        'tareas_pendientes': tareas_pendientes,
        'tareas_completadas': tareas_completadas,
    }
    return render(request, 'MyTask/index.html', contexto)


def detalle(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    registros = tarea.registros.order_by('-fecha')
    contexto = {
        'tarea': tarea,
        'registros': registros,
    }
    return render(request, 'MyTask/detalle.html', contexto)


def agregar_tarea(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if titulo:
            Tarea.objects.create(titulo=titulo, descripcion=descripcion)
    return redirect('mytask:index')


def editar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    error = ''
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if titulo:
            tarea.titulo = titulo
            tarea.descripcion = descripcion
            tarea.save()
            return redirect('mytask:detalle', tarea_id=tarea.id)
        error = 'El título no puede estar vacío.'
    return render(request, 'MyTask/editar.html', {'tarea': tarea, 'error': error})


def eliminar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    if request.method == 'POST':
        tarea.delete()
        return redirect('mytask:index')
    return redirect('mytask:detalle', tarea_id=tarea.id)


def agregar_registro(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    if request.method == 'POST':
        detalle = request.POST.get('detalle', '').strip()
        if detalle:
            tarea.registros.create(detalle=detalle)
    return redirect('mytask:detalle', tarea_id=tarea.id)


def completar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    if request.method == 'POST':
        tarea.completada = not tarea.completada
        tarea.save()
    return redirect('mytask:detalle', tarea_id=tarea.id)
