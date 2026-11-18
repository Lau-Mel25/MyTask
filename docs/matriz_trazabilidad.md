# Matriz de trazabilidad — MyTask

Relaciona cada historia de usuario (HU) del backlog con su implementación en el repositorio y con la prueba o evidencia que la valida.

Estado: **Hecho** = implementado y verificado · **En curso** = falta evidencia (por ejemplo, el video o el despliegue) · **Pendiente** = por construir.

# Entrega 2

## 1. Funcionalidad de la aplicación

| HU | Historia de usuario | Implementación (archivo / ruta) | Prueba o evidencia | Estado |
|---|---|---|---|---|
| HU01 | Crear una tarea con título y descripción | `views.agregar_tarea` · `/myTask/nueva/` · `forms.py` · modelo `Tarea` | `test_crear_tarea_asigna_propietario` | Hecho |
| HU02 | Ver mis tareas separadas en pendientes y completadas | `views.index` · `/myTask/` · `templates/MyTask/index.html` | `test_cada_usuario_solo_ve_sus_tareas`, `test_panel_muestra_tareas_totales_pendientes_y_completadas` | Hecho |
| HU03 | Ver el detalle de una tarea y su historial | `views.detalle` · `/myTask/tarea/<id>/` · `detalle.html` | `test_no_puede_ver_tarea_ajena` (acceso) · demo en video | Hecho |
| HU04 | Editar una tarea | `views.editar_tarea` · `/myTask/tarea/<id>/editar/` · `editar.html` | Demo en video (sin prueba automática) | Hecho |
| HU05 | Eliminar una tarea | `views.eliminar_tarea` · `/myTask/tarea/<id>/eliminar/` | `test_no_puede_eliminar_tarea_ajena` | Hecho |
| HU06 | Marcar una tarea como completada o pendiente | `views.completar_tarea` · `/myTask/tarea/<id>/completar/` · campo `Tarea.completada` | Demo en video (sin prueba automática) | Hecho |
| HU07 | Registrar en la bitácora lo que hice | `views.agregar_registro` · `/myTask/tarea/<id>/registro/` · modelo `Registro` | Demo en video (sin prueba automática) | Hecho |

## 2. Autenticación, roles y administración

| HU | Historia de usuario | Implementación (archivo / ruta) | Prueba o evidencia | Estado |
|---|---|---|---|---|
| HU08 | Registrarme como visitante | `views.registro` · `/registro/` · `registration/registro.html` · señal `crear_perfil` en `models.py` | `test_registro_crea_usuario_perfil_e_inicia_sesion`, `test_registro_acepta_contrasena_corta`, `test_contrasenas_distintas_muestra_mensaje_en_espanol` | Hecho |
| HU09 | Iniciar y cerrar sesión | `/login/` y `/logout/` (`auth_views` en `mysite/urls.py`) · `registration/login.html` · navegación en `base.html` | `test_login_y_logout`, `test_index_requiere_iniciar_sesion`, `test_login_incorrecto_muestra_mensaje_en_espanol` | Hecho |
| HU10 | Ver solo mis tareas | `Tarea.propietario` (FK a `User`) · filtro por usuario en `views._tarea_del_usuario` y `views.index` · `@login_required` | `test_cada_usuario_solo_ve_sus_tareas`, `test_no_puede_ver_tarea_ajena`, `test_no_puede_eliminar_tarea_ajena` | Hecho |
| HU11 | (Administrador) Asignar roles a los usuarios | Modelo `Perfil` (rol) · `views.usuarios` · `/myTask/usuarios/` · decorador `@solo_administradores` (`decorators.py`) | `test_administrador_cambia_rol_desde_la_vista`, `test_administrador_no_cambia_su_propio_rol`, `test_usuario_normal_no_entra_a_gestion_usuarios`, `test_rol_invalido_se_ignora` | Hecho |
| HU12 | (Administrador) Gestionar usuarios y tareas desde Django Admin | `admin.py` (`UserAdmin`, `TareaAdmin`, `RegistroAdmin`) · `/admin/` · sincronización rol ↔ `is_staff` en `Perfil.save` | `test_crear_usuario_con_rol_desde_admin`, `test_rol_administrador_habilita_django_admin`, `test_rol_usuario_quita_acceso_a_django_admin`, `test_administrador_entra_al_panel` | Hecho |

## 3. Docker, despliegue y documentación

| HU | Historia de usuario | Implementación (archivo / ruta) | Prueba o evidencia | Estado |
|---|---|---|---|---|
| HU13 | Dockerfile de Django | `Dockerfile` · `.dockerignore` · `requirements.txt` (Django, gunicorn, whitenoise) | `docker build -t mytask .` y `docker run` · demo en video | Hecho |
| HU14 | Despliegue inicial en la nube | Imagen del `Dockerfile` publicada · variables `DJANGO_*` en `mysite/settings.py` | URL pública: **[pegar URL del despliegue]** | Hecho |
| HU15 | Diagrama de secuencia (primera versión) | `docs/diagramas_uml.md` (sección 2) | Diagrama incluido en el SRS | Hecho |
| HU23 | Claves y configuración con variables de entorno | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_DB_PATH` en `mysite/settings.py` | Contenedor arranca con `-e` sin tocar el código | Hecho |
| HU22 | SRS, UML inicial y matriz de trazabilidad | `docs/` (SRS actualizado, `diagramas_uml.md`, este documento) | Documentos entregados | Hecho |
| HU27 | Actualizar el SRS y grabar el Video 2 | SRS actualizado | Video 2 (máx. 8 min) | En curso |

## 4. Trazabilidad con los entregables de la Entrega 2

| Entregable solicitado | Evidencia en el repositorio |
|---|---|
| Aplicación Django funcional (CRUD, login, roles, Django Admin) | `MyTask/`, `mysite/`, `templates/` · HU01–HU12 |
| Diagrama de secuencia (primera versión) | `docs/diagramas_uml.md` · HU15 |
| Diagrama de clases de los modelos | `docs/diagrama_clases_modelos.png` |
| Dockerización inicial (contenedor Django funcional) | `Dockerfile` · HU13 |
| Despliegue inicial (aplicación publicada) | URL pública · HU14 |
| SRS actualizado y matriz de trazabilidad | `docs/` · HU22, HU27 |
| Video 2 (demo 3 min + explicación técnica 2 min) | Pendiente de grabar · HU27 |

## 5. Cobertura de pruebas de la Entrega 2

Pruebas automáticas al cierre de la Entrega 2: **26** (`python manage.py test`). Las HU04, HU06 y HU07 (editar, completar y bitácora) no tienen prueba automática propia; se validan con la demo.

# Entrega 3

## 6. Entrega 3: microservicio, IA, Swagger y Compose

| HU | Historia de usuario | Implementación (archivo / ruta) | Prueba o evidencia | Estado |
|---|---|---|---|---|
| HU16 | Microservicio Node.js con API REST | `microservicio/src/app.js`, `server.js` · `POST /api/sugerencias`, `GET /health` · clave `X-API-Key` | `microservicio/tests/app.test.js` (200, 400, 401, 502, emojis, JSON mal formado) · despliegue pendiente de publicar | En curso |
| HU17 | Swagger público para probar los endpoints | `microservicio/openapi.yaml` · `swagger-ui-express` en `/api-docs` | `microservicio/tests/docs.test.js` · URL pública pendiente | En curso |
| HU18 | Django consume el microservicio | `MyTask/sugerencias.py` (`pedir_sugerencias`) · `NODE_SERVICE_URL`, `INTERNAL_API_KEY`, `SUGERENCIAS_TIMEOUT` en `settings.py` | `ClienteSugerenciasTests` (8 pruebas: éxito, cabeceras, 502, 401, servicio apagado, tiempo agotado, respuesta inválida) | Hecho |
| HU19 | La IA sugiere subtareas | `microservicio/src/gemini.js` (`generarSubtareas`) · vistas `sugerir_subtareas` y `agregar_sugerencias` · `detalle.html` | `gemini.test.js` (10), `SugerenciasViewsTests` (10) con la IA simulada · prueba real con clave de Gemini pendiente | En curso |
| HU20 | Aviso claro si la IA falla | `SugerenciasNoDisponibles` · `messages.error` en la vista · Node responde 502 con mensaje en español | `test_sugerir_con_servicio_caido_muestra_aviso_y_la_pagina_carga`, `lanza IAError si Gemini responde 429` | Hecho |
| HU21 | Docker Compose para levantar todo con un comando | `docker-compose.yml` · `microservicio/Dockerfile` · `.env.example` | YAML validado; `docker compose up` sin probar (Docker no instalado en el equipo de desarrollo) | En curso |
| HU24 | README profesional y pruebas automáticas básicas | `README.md` · pruebas Django y Jest | 44 pruebas de Django y 32 de Node | Hecho |
| HU28 | Actualizar SRS, UML y matriz, y grabar el Video 3 | `docs/SRS_entrega3_actualizacion.md`, `docs/diagramas_uml.md` y PNG, este documento | Video 3 pendiente | En curso |
| HU29 | Despliegue final, video final y sustentación | `docs/despliegue.md` (guía) | Entrega final del 26/11 | Pendiente |

### Cobertura de pruebas de la Entrega 3

- **Django:** `python manage.py test` → **44** pruebas (26 anteriores y 18 nuevas).
- **Node:** `npm test` en `microservicio/` → **32** pruebas (`gemini` 10, `app` 16, `docs` 6).
- Ninguna prueba automática llama a Gemini de verdad; la IA se simula. La prueba real es manual con una clave propia.
