from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import solo_administradores
from .forms import RegistroForm
from .models import Perfil, Tarea


def _tarea_del_usuario(request, tarea_id):
    """Devuelve la tarea solo si pertenece al usuario autenticado."""
    return get_object_or_404(Tarea, pk=tarea_id, propietario=request.user)


@login_required
def index(request):
    tareas_pendientes = Tarea.objects.filter(
        propietario=request.user, completada=False
    ).order_by('-fecha_creacion')
    tareas_completadas = Tarea.objects.filter(
        propietario=request.user, completada=True
    ).order_by('-fecha_creacion')
    contexto = {
        'tareas_pendientes': tareas_pendientes,
        'tareas_completadas': tareas_completadas,
    }
    return render(request, 'MyTask/index.html', contexto)


@login_required
def detalle(request, tarea_id):
    tarea = _tarea_del_usuario(request, tarea_id)
    registros = tarea.registros.order_by('-fecha')
    contexto = {
        'tarea': tarea,
        'registros': registros,
    }
    return render(request, 'MyTask/detalle.html', contexto)


@login_required
def agregar_tarea(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if titulo:
            Tarea.objects.create(
                propietario=request.user,
                titulo=titulo,
                descripcion=descripcion,
            )
        else:
            messages.error(request, 'El título de la tarea no puede estar vacío.')
    return redirect('mytask:index')


@login_required
def editar_tarea(request, tarea_id):
    tarea = _tarea_del_usuario(request, tarea_id)
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


@login_required
def eliminar_tarea(request, tarea_id):
    tarea = _tarea_del_usuario(request, tarea_id)
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'La tarea se eliminó correctamente.')
        return redirect('mytask:index')
    return redirect('mytask:detalle', tarea_id=tarea.id)


@login_required
def agregar_registro(request, tarea_id):
    tarea = _tarea_del_usuario(request, tarea_id)
    if request.method == 'POST':
        detalle = request.POST.get('detalle', '').strip()
        if detalle:
            tarea.registros.create(detalle=detalle)
    return redirect('mytask:detalle', tarea_id=tarea.id)


@login_required
def completar_tarea(request, tarea_id):
    tarea = _tarea_del_usuario(request, tarea_id)
    if request.method == 'POST':
        tarea.completada = not tarea.completada
        tarea.save()
    return redirect('mytask:detalle', tarea_id=tarea.id)


def registro(request):
    """Registro de un visitante; al crearse la cuenta inicia sesión."""
    if request.user.is_authenticated:
        return redirect('mytask:index')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(
                request,
                f'¡Bienvenido, {usuario.username}! Tu cuenta fue creada correctamente.',
            )
            return redirect('mytask:index')
    else:
        form = RegistroForm()

    return render(request, 'registration/registro.html', {'form': form})


@solo_administradores
def panel(request):
    """Panel de administración de la app: usuarios, roles y tareas."""
    usuarios = (
        User.objects.select_related('perfil')
        .annotate(
            total_tareas=Count('tareas', distinct=True),
            tareas_pendientes=Count(
                'tareas', filter=Q(tareas__completada=False), distinct=True
            ),
            tareas_completadas=Count(
                'tareas', filter=Q(tareas__completada=True), distinct=True
            ),
        )
        .order_by('username')
    )
    tareas = Tarea.objects.select_related('propietario').order_by('-fecha_creacion')
    contexto = {
        'usuarios': usuarios,
        'tareas': tareas,
        'total_usuarios': usuarios.count(),
        'total_tareas': tareas.count(),
        'total_completadas': tareas.filter(completada=True).count(),
    }
    return render(request, 'MyTask/panel.html', contexto)


@solo_administradores
def usuarios(request):
    """Gestión de roles en una vista propia, separada de Django Admin."""
    lista_usuarios = (
        User.objects.select_related('perfil')
        .annotate(
            total_tareas=Count('tareas', distinct=True),
            tareas_pendientes=Count(
                'tareas', filter=Q(tareas__completada=False), distinct=True
            ),
            tareas_completadas=Count(
                'tareas', filter=Q(tareas__completada=True), distinct=True
            ),
        )
        .order_by('username')
    )

    if request.method == 'POST':
        roles_validos = dict(Perfil.Rol.choices)
        cambios = 0

        for usuario in lista_usuarios:
            # El superusuario y el propio administrador no se pueden degradar.
            if usuario.is_superuser or usuario.pk == request.user.pk:
                continue

            nuevo_rol = request.POST.get(f'rol_{usuario.pk}')
            if nuevo_rol not in roles_validos:
                continue

            perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
            if perfil.rol != nuevo_rol:
                perfil.rol = nuevo_rol
                perfil.save()
                cambios += 1

        if cambios:
            messages.success(
                request,
                f'Se actualizaron {cambios} rol(es) correctamente.',
            )
        else:
            messages.info(request, 'No se realizaron cambios en los roles.')
        return redirect('mytask:usuarios')

    contexto = {
        'usuarios': lista_usuarios,
        'roles': Perfil.Rol.choices,
    }
    return render(request, 'MyTask/usuarios.html', contexto)
