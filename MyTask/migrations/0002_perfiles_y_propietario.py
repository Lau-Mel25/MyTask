import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def asignar_propietario(apps, schema_editor):
    """Asigna las tareas existentes al primer usuario disponible."""
    Tarea = apps.get_model('MyTask', 'Tarea')
    User = apps.get_model('auth', 'User')

    tareas_sin_duenio = Tarea.objects.filter(propietario__isnull=True)
    if not tareas_sin_duenio.exists():
        return

    propietario = (
        User.objects.filter(is_superuser=True).order_by('id').first()
        or User.objects.order_by('id').first()
    )
    if propietario is None:
        raise RuntimeError(
            'Hay tareas sin propietario y no existe ningún usuario. '
            'Crea un superusuario con "python manage.py createsuperuser" '
            'y vuelve a ejecutar "python manage.py migrate".'
        )

    tareas_sin_duenio.update(propietario=propietario)


def crear_perfiles(apps, schema_editor):
    """Crea el perfil de los usuarios que ya existían."""
    User = apps.get_model('auth', 'User')
    Perfil = apps.get_model('MyTask', 'Perfil')

    for usuario in User.objects.all():
        rol = 'administrador' if usuario.is_superuser else 'usuario'
        Perfil.objects.get_or_create(usuario=usuario, defaults={'rol': rol})


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('MyTask', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('usuario', 'Usuario'), ('administrador', 'Administrador')], default='usuario', max_length=20)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'perfil',
                'verbose_name_plural': 'perfiles',
            },
        ),
        migrations.AddField(
            model_name='tarea',
            name='propietario',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tareas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='propietario',
            ),
        ),
        migrations.RunPython(asignar_propietario, migrations.RunPython.noop),
        migrations.RunPython(crear_perfiles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='tarea',
            name='propietario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tareas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='propietario',
            ),
        ),
        migrations.AlterModelOptions(
            name='tarea',
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'tarea', 'verbose_name_plural': 'tareas'},
        ),
        migrations.AlterModelOptions(
            name='registro',
            options={'ordering': ['-fecha'], 'verbose_name': 'registro', 'verbose_name_plural': 'registros'},
        ),
    ]
