import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Perfil, Tarea
from .sugerencias import SugerenciasNoDisponibles, pedir_sugerencias


class AutenticacionTests(TestCase):
    def test_index_requiere_iniciar_sesion(self):
        respuesta = self.client.get(reverse('mytask:index'))
        self.assertRedirects(
            respuesta,
            f"{reverse('login')}?next={reverse('mytask:index')}",
        )

    def test_registro_crea_usuario_perfil_e_inicia_sesion(self):
        respuesta = self.client.post(
            reverse('registro'),
            {
                'username': 'nuevo',
                'email': 'nuevo@example.com',
                'password1': 'ClaveSegura123',
                'password2': 'ClaveSegura123',
            },
        )
        self.assertRedirects(respuesta, reverse('mytask:index'))

        usuario = User.objects.get(username='nuevo')
        self.assertEqual(usuario.perfil.rol, Perfil.Rol.USUARIO)
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_login_y_logout(self):
        User.objects.create_user('ana', password='ClaveSegura123')

        self.assertTrue(
            self.client.login(username='ana', password='ClaveSegura123')
        )
        respuesta = self.client.post(reverse('logout'))
        self.assertRedirects(respuesta, reverse('login'))


class TareasPorUsuarioTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', password='ClaveSegura123')
        self.luis = User.objects.create_user('luis', password='ClaveSegura123')
        self.tarea_ana = Tarea.objects.create(
            propietario=self.ana, titulo='Tarea de Ana'
        )
        self.tarea_luis = Tarea.objects.create(
            propietario=self.luis, titulo='Tarea de Luis'
        )

    def test_cada_usuario_solo_ve_sus_tareas(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse('mytask:index'))
        self.assertContains(respuesta, 'Tarea de Ana')
        self.assertNotContains(respuesta, 'Tarea de Luis')

    def test_no_puede_ver_tarea_ajena(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(
            reverse('mytask:detalle', args=[self.tarea_luis.id])
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_no_puede_eliminar_tarea_ajena(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(
            reverse('mytask:eliminar_tarea', args=[self.tarea_luis.id])
        )
        self.assertEqual(respuesta.status_code, 404)
        self.assertTrue(Tarea.objects.filter(pk=self.tarea_luis.pk).exists())

    def test_crear_tarea_asigna_propietario(self):
        self.client.force_login(self.ana)
        self.client.post(
            reverse('mytask:agregar_tarea'),
            {'titulo': 'Nueva', 'descripcion': ''},
        )
        tarea = Tarea.objects.get(titulo='Nueva')
        self.assertEqual(tarea.propietario, self.ana)


class RolesTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', password='ClaveSegura123')
        self.admin.perfil.rol = Perfil.Rol.ADMINISTRADOR
        self.admin.perfil.save()

        self.usuario = User.objects.create_user(
            'usuario', password='ClaveSegura123'
        )

    def test_usuario_normal_no_entra_al_panel(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('mytask:panel'))
        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_entra_al_panel(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse('mytask:panel'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'usuario')

    def test_rol_administrador_habilita_django_admin(self):
        self.assertFalse(self.usuario.is_staff)

        self.usuario.perfil.rol = Perfil.Rol.ADMINISTRADOR
        self.usuario.perfil.save()
        self.usuario.refresh_from_db()

        self.assertTrue(self.usuario.is_staff)
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

    def test_rol_usuario_quita_acceso_a_django_admin(self):
        self.admin.perfil.rol = Perfil.Rol.USUARIO
        self.admin.perfil.save()
        self.admin.refresh_from_db()

        self.assertFalse(self.admin.is_staff)

    def test_superusuario_es_administrador(self):
        root = User.objects.create_superuser(
            'root', 'root@example.com', 'ClaveSegura123'
        )
        self.assertTrue(root.perfil.es_administrador)
        self.client.force_login(root)
        respuesta = self.client.get(reverse('mytask:panel'))
        self.assertEqual(respuesta.status_code, 200)


class ConteoTareasTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin_conteo', password='ClaveSegura123'
        )
        self.admin.perfil.rol = Perfil.Rol.ADMINISTRADOR
        self.admin.perfil.save()

        self.usuario = User.objects.create_user(
            'usuario_conteo', password='ClaveSegura123'
        )
        Tarea.objects.create(
            propietario=self.usuario, titulo='Pendiente 1', completada=False
        )
        Tarea.objects.create(
            propietario=self.usuario, titulo='Pendiente 2', completada=False
        )
        Tarea.objects.create(
            propietario=self.usuario, titulo='Completada', completada=True
        )
        self.client.force_login(self.admin)

    def _conteo(self, respuesta):
        usuarios = list(respuesta.context['usuarios'])
        return next(u for u in usuarios if u.pk == self.usuario.pk)

    def test_panel_muestra_tareas_totales_pendientes_y_completadas(self):
        respuesta = self.client.get(reverse('mytask:panel'))
        usuario = self._conteo(respuesta)
        self.assertEqual(usuario.total_tareas, 3)
        self.assertEqual(usuario.tareas_pendientes, 2)
        self.assertEqual(usuario.tareas_completadas, 1)
        self.assertContains(respuesta, '<th>Pendientes</th>', html=True)

    def test_gestion_usuarios_muestra_tareas_totales_pendientes_y_completadas(self):
        respuesta = self.client.get(reverse('mytask:usuarios'))
        usuario = self._conteo(respuesta)
        self.assertEqual(usuario.total_tareas, 3)
        self.assertEqual(usuario.tareas_pendientes, 2)
        self.assertEqual(usuario.tareas_completadas, 1)
        self.assertContains(respuesta, '<th>Pendientes</th>', html=True)


class GestionRolesTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin_roles', password='ClaveSegura123'
        )
        self.admin.perfil.rol = Perfil.Rol.ADMINISTRADOR
        self.admin.perfil.save()

        self.usuario = User.objects.create_user(
            'usuario_roles', password='ClaveSegura123'
        )
        self.client.force_login(self.admin)

    def test_usuario_normal_no_entra_a_gestion_usuarios(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('mytask:usuarios'))
        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_ve_el_select_de_roles(self):
        respuesta = self.client.get(reverse('mytask:usuarios'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, f'name="rol_{self.usuario.pk}"')
        self.assertContains(respuesta, '<select')

    def test_administrador_cambia_rol_desde_la_vista(self):
        respuesta = self.client.post(
            reverse('mytask:usuarios'),
            {f'rol_{self.usuario.pk}': Perfil.Rol.ADMINISTRADOR},
        )
        self.assertRedirects(respuesta, reverse('mytask:usuarios'))

        perfil = Perfil.objects.get(usuario=self.usuario)
        self.assertEqual(perfil.rol, Perfil.Rol.ADMINISTRADOR)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_staff)

    def test_administrador_no_cambia_su_propio_rol(self):
        respuesta = self.client.post(
            reverse('mytask:usuarios'),
            {f'rol_{self.admin.pk}': Perfil.Rol.USUARIO},
        )
        self.assertRedirects(respuesta, reverse('mytask:usuarios'))

        perfil = Perfil.objects.get(usuario=self.admin)
        self.assertEqual(perfil.rol, Perfil.Rol.ADMINISTRADOR)

    def test_superusuario_conserva_su_rol(self):
        root = User.objects.create_superuser(
            'root_roles', 'root@example.com', 'ClaveSegura123'
        )
        self.client.force_login(root)
        self.client.post(
            reverse('mytask:usuarios'),
            {f'rol_{root.pk}': Perfil.Rol.USUARIO},
        )

        perfil = Perfil.objects.get(usuario=root)
        self.assertEqual(perfil.rol, Perfil.Rol.ADMINISTRADOR)

    def test_rol_invalido_se_ignora(self):
        self.client.post(
            reverse('mytask:usuarios'),
            {f'rol_{self.usuario.pk}': 'rol_inventado'},
        )

        perfil = Perfil.objects.get(usuario=self.usuario)
        self.assertEqual(perfil.rol, Perfil.Rol.USUARIO)


class AdminUsuariosTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(
            'root', 'root@example.com', 'ClaveSegura123'
        )
        self.client.force_login(self.root)

    def test_crear_usuario_con_rol_desde_admin(self):
        respuesta = self.client.post(
            reverse('admin:auth_user_add'),
            {
                'username': 'nuevo_admin',
                'usable_password': 'true',
                'password1': 'ClaveSegura123',
                'password2': 'ClaveSegura123',
                'perfil-TOTAL_FORMS': '1',
                'perfil-INITIAL_FORMS': '0',
                'perfil-MIN_NUM_FORMS': '0',
                'perfil-MAX_NUM_FORMS': '1',
                'perfil-0-rol': 'administrador',
                'perfil-0-id': '',
                'perfil-0-usuario': '',
            },
        )
        self.assertEqual(respuesta.status_code, 302)

        usuario = User.objects.get(username='nuevo_admin')
        self.assertEqual(usuario.perfil.rol, Perfil.Rol.ADMINISTRADOR)


class MensajesEnEspanolTests(TestCase):
    def test_login_incorrecto_muestra_mensaje_en_espanol(self):
        respuesta = self.client.post(
            reverse('login'),
            {'username': 'no_existe', 'password': 'incorrecta'},
        )
        errores = respuesta.context['form'].non_field_errors()
        self.assertTrue(errores)
        self.assertIn('correctos', str(errores[0]))

    def test_registro_acepta_contrasena_corta(self):
        """Los validadores están desactivados temporalmente."""
        respuesta = self.client.post(
            reverse('registro'),
            {
                'username': 'clave_corta',
                'email': '',
                'password1': '123',
                'password2': '123',
            },
        )
        self.assertRedirects(respuesta, reverse('mytask:index'))
        self.assertTrue(User.objects.filter(username='clave_corta').exists())

    def test_contrasenas_distintas_muestra_mensaje_en_espanol(self):
        respuesta = self.client.post(
            reverse('registro'),
            {
                'username': 'claves_distintas',
                'email': '',
                'password1': '123',
                'password2': '456',
            },
        )
        self.assertContains(respuesta, 'no coinciden')

    def test_pagina_403_en_espanol(self):
        usuario = User.objects.create_user(
            'sin_permisos', password='ClaveSegura123'
        )
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse('mytask:panel'))
        self.assertContains(respuesta, 'Acceso denegado', status_code=403)

    def test_pagina_404_en_espanol(self):
        usuario = User.objects.create_user(
            'sin_tarea', password='ClaveSegura123'
        )
        otro = User.objects.create_user('duenio', password='ClaveSegura123')
        tarea = Tarea.objects.create(propietario=otro, titulo='Tarea ajena')

        self.client.force_login(usuario)
        respuesta = self.client.get(
            reverse('mytask:detalle', args=[tarea.id])
        )
        self.assertContains(respuesta, 'Página no encontrada', status_code=404)


def _respuesta_http(cuerpo):
    """Simula la respuesta de urlopen (administrador de contexto con read())."""
    if not isinstance(cuerpo, bytes):
        cuerpo = json.dumps(cuerpo).encode('utf-8')
    respuesta = MagicMock()
    respuesta.read.return_value = cuerpo
    respuesta.__enter__.return_value = respuesta
    return respuesta


def _error_http(codigo, cuerpo):
    return HTTPError(
        'http://nodo:3000/api/sugerencias',
        codigo,
        'error',
        {},
        io.BytesIO(json.dumps(cuerpo).encode('utf-8')),
    )


@override_settings(
    NODE_SERVICE_URL='http://nodo:3000',
    INTERNAL_API_KEY='clave-de-prueba',
    SUGERENCIAS_TIMEOUT=5,
)
class ClienteSugerenciasTests(TestCase):
    def setUp(self):
        usuario = User.objects.create_user('ana', password='ClaveSegura123')
        self.tarea = Tarea.objects.create(
            propietario=usuario, titulo='Preparar informe', descripcion='Entrega del viernes'
        )

    @patch('MyTask.sugerencias.urlopen')
    def test_devuelve_la_lista_de_subtareas(self, urlopen):
        urlopen.return_value = _respuesta_http(
            {'tarea': 'Preparar informe', 'subtareas': ['a', 'b', 'c']}
        )
        self.assertEqual(pedir_sugerencias(self.tarea), ['a', 'b', 'c'])

    @patch('MyTask.sugerencias.urlopen')
    def test_envia_titulo_descripcion_y_clave(self, urlopen):
        urlopen.return_value = _respuesta_http({'subtareas': ['a', 'b', 'c']})
        pedir_sugerencias(self.tarea)
        peticion = urlopen.call_args[0][0]
        self.assertEqual(peticion.get_method(), 'POST')
        self.assertEqual(peticion.full_url, 'http://nodo:3000/api/sugerencias')
        self.assertEqual(peticion.get_header('X-api-key'), 'clave-de-prueba')
        self.assertEqual(peticion.get_header('Content-type'), 'application/json')
        self.assertEqual(
            json.loads(peticion.data),
            {'titulo': 'Preparar informe', 'descripcion': 'Entrega del viernes'},
        )
        self.assertEqual(urlopen.call_args[1]['timeout'], 5)

    @patch('MyTask.sugerencias.urlopen')
    def test_error_502_muestra_el_mensaje_del_servicio(self, urlopen):
        urlopen.side_effect = _error_http(502, {'error': 'La IA alcanzó su límite de uso.'})
        with self.assertRaises(SugerenciasNoDisponibles) as contexto:
            pedir_sugerencias(self.tarea)
        self.assertEqual(str(contexto.exception), 'La IA alcanzó su límite de uso.')

    @patch('MyTask.sugerencias.urlopen')
    def test_error_401_no_filtra_detalles_y_lanza_sugerencias_no_disponibles(self, urlopen):
        urlopen.side_effect = _error_http(401, {'error': 'Clave de API ausente o incorrecta.'})
        with self.assertRaises(SugerenciasNoDisponibles) as contexto:
            pedir_sugerencias(self.tarea)
        self.assertNotIn('Clave', str(contexto.exception))

    @patch('MyTask.sugerencias.urlopen')
    def test_servicio_apagado_lanza_sugerencias_no_disponibles(self, urlopen):
        urlopen.side_effect = URLError('conexion rechazada')
        with self.assertRaises(SugerenciasNoDisponibles):
            pedir_sugerencias(self.tarea)

    @patch('MyTask.sugerencias.urlopen')
    def test_tiempo_agotado_lanza_sugerencias_no_disponibles(self, urlopen):
        urlopen.side_effect = TimeoutError()
        with self.assertRaises(SugerenciasNoDisponibles):
            pedir_sugerencias(self.tarea)

    @patch('MyTask.sugerencias.urlopen')
    def test_respuesta_que_no_es_json_lanza_sugerencias_no_disponibles(self, urlopen):
        urlopen.return_value = _respuesta_http(b'<html>no es json</html>')
        with self.assertRaises(SugerenciasNoDisponibles):
            pedir_sugerencias(self.tarea)

    @patch('MyTask.sugerencias.urlopen')
    def test_respuesta_sin_lista_de_subtareas_lanza_sugerencias_no_disponibles(self, urlopen):
        urlopen.return_value = _respuesta_http({'tarea': 'x'})
        with self.assertRaises(SugerenciasNoDisponibles):
            pedir_sugerencias(self.tarea)


class SugerenciasViewsTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', password='ClaveSegura123')
        self.luis = User.objects.create_user('luis', password='ClaveSegura123')
        self.tarea_ana = Tarea.objects.create(
            propietario=self.ana, titulo='Preparar informe'
        )
        self.tarea_luis = Tarea.objects.create(
            propietario=self.luis, titulo='Tarea de Luis'
        )
        self.url_sugerir = reverse('mytask:sugerir_subtareas', args=[self.tarea_ana.id])
        self.url_agregar = reverse('mytask:agregar_sugerencias', args=[self.tarea_ana.id])

    @patch('MyTask.views.pedir_sugerencias')
    def test_sugerir_muestra_las_sugerencias_en_el_detalle(self, pedir):
        pedir.return_value = ['Reunir datos', 'Escribir borrador', 'Revisar y entregar']
        self.client.force_login(self.ana)
        respuesta = self.client.post(self.url_sugerir)
        self.assertEqual(respuesta.status_code, 200)
        for sugerencia in pedir.return_value:
            self.assertContains(respuesta, sugerencia)
        self.assertContains(respuesta, 'Agregar como tareas')
        pedir.assert_called_once_with(self.tarea_ana)

    @patch('MyTask.views.pedir_sugerencias')
    def test_sugerir_con_servicio_caido_muestra_aviso_y_la_pagina_carga(self, pedir):
        pedir.side_effect = SugerenciasNoDisponibles('La IA alcanzó su límite de uso.')
        self.client.force_login(self.ana)
        respuesta = self.client.post(self.url_sugerir)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'La IA alcanzó su límite de uso.')
        self.assertContains(respuesta, 'Bitácora de avances')
        self.assertNotContains(respuesta, 'Agregar como tareas')

    @patch('MyTask.views.pedir_sugerencias')
    def test_sugerir_tarea_ajena_devuelve_404_y_no_llama_al_servicio(self, pedir):
        self.client.force_login(self.luis)
        respuesta = self.client.post(self.url_sugerir)
        self.assertEqual(respuesta.status_code, 404)
        pedir.assert_not_called()

    def test_sugerir_requiere_login(self):
        respuesta = self.client.post(self.url_sugerir)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn('/login/', respuesta.url)

    def test_sugerir_y_agregar_por_get_devuelven_405(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(self.url_sugerir).status_code, 405)
        self.assertEqual(self.client.get(self.url_agregar).status_code, 405)

    def test_agregar_crea_una_tarea_por_cada_titulo_marcado(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(
            self.url_agregar, {'sugerencia': ['Reunir datos', 'Escribir borrador']}
        )
        self.assertRedirects(respuesta, reverse('mytask:index'))
        nuevas = Tarea.objects.filter(propietario=self.ana).exclude(pk=self.tarea_ana.pk)
        self.assertEqual(
            sorted(nuevas.values_list('titulo', flat=True)),
            ['Escribir borrador', 'Reunir datos'],
        )
        self.assertFalse(nuevas.filter(completada=True).exists())

    def test_agregar_recorta_a_100_descarta_vacios_y_limita_a_6(self):
        self.client.force_login(self.ana)
        titulos = ['uno', '', '   ', 'x' * 150, 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete']
        self.client.post(self.url_agregar, {'sugerencia': titulos})
        nuevas = Tarea.objects.filter(propietario=self.ana).exclude(pk=self.tarea_ana.pk)
        self.assertEqual(nuevas.count(), 6)
        self.assertFalse(nuevas.filter(titulo='').exists())
        self.assertTrue(nuevas.filter(titulo='x' * 100).exists())

    def test_agregar_sin_titulos_no_crea_nada_y_avisa(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(self.url_agregar, {}, follow=True)
        self.assertEqual(Tarea.objects.filter(propietario=self.ana).count(), 1)
        self.assertContains(respuesta, 'No seleccionaste ninguna sugerencia.')

    def test_agregar_tarea_ajena_devuelve_404_y_no_crea_tareas(self):
        self.client.force_login(self.luis)
        respuesta = self.client.post(self.url_agregar, {'sugerencia': ['Intruso']})
        self.assertEqual(respuesta.status_code, 404)
        self.assertFalse(Tarea.objects.filter(titulo='Intruso').exists())

    def test_detalle_muestra_el_boton_sugerir_subtareas(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse('mytask:detalle', args=[self.tarea_ana.id]))
        self.assertContains(respuesta, 'Sugerir subtareas')
        self.assertContains(respuesta, self.url_sugerir)


@override_settings(
    NODE_SERVICE_URL='http://nodo:3000',
    INTERNAL_API_KEY='clave-de-prueba',
    SUGERENCIAS_TIMEOUT=5,
)
class ClienteSugerenciasRobustezTests(TestCase):
    def setUp(self):
        usuario = User.objects.create_user('ana', password='ClaveSegura123')
        self.usuario = usuario

    @patch('MyTask.sugerencias.urlopen')
    def test_recorta_titulo_y_descripcion_a_los_limites_del_servicio(self, urlopen):
        urlopen.return_value = _respuesta_http({'subtareas': ['a', 'b', 'c']})
        tarea = Tarea.objects.create(
            propietario=self.usuario, titulo='t' * 100, descripcion='d' * 1500
        )
        pedir_sugerencias(tarea)
        enviado = json.loads(urlopen.call_args[0][0].data)
        self.assertEqual(len(enviado['descripcion']), 1000)
        self.assertEqual(len(enviado['titulo']), 100)

    @patch('MyTask.sugerencias.urlopen')
    def test_registra_en_el_log_el_fallo_del_servicio(self, urlopen):
        urlopen.side_effect = _error_http(401, {'error': 'Clave de API ausente o incorrecta.'})
        tarea = Tarea.objects.create(propietario=self.usuario, titulo='x')
        with self.assertLogs('MyTask.sugerencias', level='WARNING') as registro:
            with self.assertRaises(SugerenciasNoDisponibles):
                pedir_sugerencias(tarea)
        self.assertIn('401', '\n'.join(registro.output))

    @patch('MyTask.sugerencias.urlopen')
    def test_registra_en_el_log_cuando_no_hay_conexion(self, urlopen):
        urlopen.side_effect = URLError('conexion rechazada')
        tarea = Tarea.objects.create(propietario=self.usuario, titulo='x')
        with self.assertLogs('MyTask.sugerencias', level='WARNING') as registro:
            with self.assertRaises(SugerenciasNoDisponibles):
                pedir_sugerencias(tarea)
        self.assertIn('conexion rechazada', '\n'.join(registro.output))
