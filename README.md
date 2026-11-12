# Gestor de Tareas

Aplicación web para gestionar tareas personales con una **bitácora de avances**: además de anotar qué hay que hacer, permite registrar qué se hizo y cuándo. En las próximas entregas incorporará autenticación con roles, un microservicio en Node.js y sugerencias de subtareas con IA generativa.

Ingeniería de Software · Docente: Elfar Didier Morantes Sánchez.

## Integrantes

- Daniel Santiago Chacón Olaya
- Laura Julieth Melo Ramirez

## Estado del proyecto

| Entrega | Fecha | Contenido | Estado |
|---|---|---|---|
| 1 | 05/11/2026 | SRS, UML inicial, backlog, repositorio y video | En curso |
| 2 | 12/11/2026 | CRUD, login, roles, Django Admin, Docker y despliegue inicial | En curso |
| 3 | 19/11/2026 | Microservicio Node.js, Swagger, IA, Docker Compose | Pendiente |
| Final | 26/11/2026 | Sustentación | Pendiente |

### Funcionalidades actuales (app `MyTask`)

- Registro de visitantes y creación automática de su perfil.
- Inicio y cierre de sesión.
- Roles de **usuario** y **administrador**.
- Cada usuario ve y gestiona únicamente sus propias tareas.
- Crear tareas con título y descripción.
- Listar tareas pendientes y completadas.
- Ver el detalle de una tarea y su bitácora.
- Editar y eliminar tareas.
- Marcar una tarea como completada o pendiente.
- Registrar avances en la bitácora de cada tarea.
- Panel de administración de la app con usuarios, roles, conteo de tareas (todas, pendientes y completadas) y todas las tareas.
- Gestión de usuarios y roles desde la vista `/myTask/usuarios/` con selector, además de Django Admin.

### Funcionalidades planeadas

- Microservicio en Node.js con API REST documentada con Swagger/OpenAPI.
- Sugerencia de subtareas con IA generativa.
- Contenedores con Docker y Docker Compose.

## Roles y permisos

| Rol | Permisos |
|---|---|
| **Usuario** | Se registra, inicia sesión y gestiona solo sus propias tareas y su bitácora. No puede ver ni modificar tareas de otros usuarios. |
| **Administrador** | Además de lo anterior, entra al panel `/myTask/panel/`, consulta todos los usuarios y tareas, asigna roles desde `/myTask/usuarios/` y usa Django Admin para administrar los datos. |

El rol se guarda en el modelo `Perfil` (relación uno a uno con el usuario de Django). Al registrarse, cada persona recibe el rol **Usuario**; los superusuarios se crean como **Administrador**. Para cambiar el rol de una persona: **Panel → Gestionar roles** (`/myTask/usuarios/`) y elige el rol en el selector; también sigue disponible **Django Admin → Usuarios → (usuario) → Perfil y rol**.

En la vista de gestión de roles, el administrador no puede cambiar su propio rol ni el de un superusuario, para evitar dejar el sistema sin administradores.

Al asignar el rol **Administrador**, el sistema activa automáticamente el *Staff status* para que la persona pueda entrar a `/admin/`; si se le devuelve a **Usuario**, se desactiva ese acceso. Así el rol y el panel administrativo quedan siempre sincronizados.

## Idioma y contraseñas

- Toda la interfaz, los formularios, los avisos y las páginas de error están en español (`LANGUAGE_CODE = 'es-co'`). Esto incluye los mensajes propios de Django, el login y Django Admin.
- Por ahora las **validaciones de contraseña están desactivadas** (`AUTH_PASSWORD_VALIDATORS = []`) para facilitar las pruebas. Antes de publicar la aplicación, vuelve a activarlas en `mysite/settings.py`.
- Se agregaron páginas de error en español para los códigos 400, 403, 403 por CSRF, 404 y 500.

## Diseño e interfaz

- La interfaz usa únicamente **modo claro**, con una paleta basada en tonos crema, ciruela, arena y rosa empolvado: `#f2e9e4` (fondo), `#ffffff` (superficies), `#22223b` (texto y barra superior), `#4a4e69` (acentos y botones), `#998b98` (ciruela), `#c7ac8f` (arena) y `#caada7` (rosa).
- El diseño es adaptable a móvil, tablet y escritorio, con menú plegable, tablas desplazables, formularios de una columna en pantallas pequeñas y estados de foco visibles.

## Trazabilidad de la Entrega 2

| HU | Funcionalidad | Implementación | Pruebas |
|---|---|---|---|
| **HU08** | Registro de visitante | `/registro/`, vista `registro` y plantilla `registration/registro.html` | `test_registro_crea_usuario_perfil_e_inicia_sesion` |
| **HU09** | Iniciar y cerrar sesión | `/login/`, `/logout/` y navegación en `templates/base.html` | `test_login_y_logout`, `test_index_requiere_iniciar_sesion` |
| **HU10** | Ver solo mis tareas | `Tarea.propietario` y filtros por usuario en `MyTask/views.py` | `test_cada_usuario_solo_ve_sus_tareas`, `test_no_puede_ver_tarea_ajena`, `test_no_puede_eliminar_tarea_ajena` |
| **HU11** | Asignar roles a usuarios | vista `/myTask/usuarios/` con selector de roles, modelo `Perfil` e inline en `MyTask/admin.py` | `test_administrador_cambia_rol_desde_la_vista`, `test_administrador_no_cambia_su_propio_rol`, `test_crear_usuario_con_rol_desde_admin` |
| **HU12** | Gestionar usuarios y tareas desde Django Admin | `UserAdmin`, `TareaAdmin` y `RegistroAdmin` en `MyTask/admin.py` | `test_administrador_entra_al_panel`, `test_crear_usuario_con_rol_desde_admin` |

## Tecnologías

| Componente | Tecnología |
|---|---|
| Aplicación web | Python y Django |
| Base de datos | SQLite (desarrollo) |
| Microservicio *(planeado)* | Node.js |
| IA *(planeado)* | API de IA generativa |
| Contenedores *(planeado)* | Docker y Docker Compose |
| Documentación de API *(planeado)* | Swagger / OpenAPI |
| Control de versiones | GitHub |

## Arquitectura

```
Usuario (navegador) → Django → Node.js → API de IA
                         │
                         └→ Base de datos
```

El usuario solo habla con Django. Django guarda los datos en la base de datos y le pide las sugerencias de IA al microservicio Node.js, que es el único que consulta al proveedor de IA. Los diagramas UML están en la documentación (SRS).

## Estructura del repositorio

```
.
├── manage.py
├── mysite/        # configuración del proyecto Django (settings, URLs)
├── MyTask/        # app del gestor de tareas (modelos, vistas, formularios, tests)
├── templates/     # plantillas compartidas: base, login y registro
├── .gitignore
└── README.md
```

## Cómo ejecutarlo en local

Requisitos: Python 3.12 o superior.

1. Clonar el repositorio y entrar a la carpeta del proyecto:

   ```bash
   git clone <URL-del-repositorio>
   cd <carpeta-del-proyecto>
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv .venv
   ```

   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - Linux o macOS: `source .venv/bin/activate`

3. Instalar las dependencias:

   ```bash
   pip install django
   ```

4. Crear las tablas de la base de datos:

   ```bash
   python manage.py migrate
   ```

5. (Opcional) Crear un superusuario para entrar al panel de administración:

   ```bash
   python manage.py createsuperuser
   ```

6. Iniciar el servidor:

   ```bash
   python manage.py runserver
   ```

- Aplicación: `http://127.0.0.1:8000/` (redirige a las tareas; si no hay sesión, al login).
- Registro: `http://127.0.0.1:8000/registro/`
- Login: `http://127.0.0.1:8000/login/`
- Panel de la app (solo administradores): `http://127.0.0.1:8000/myTask/panel/`
- Django Admin: `http://127.0.0.1:8000/admin/`

### Pruebas automáticas

```bash
python manage.py test
```

Las pruebas cubren el registro, el login/logout, el aislamiento de tareas por usuario y la restricción del panel a administradores.

## Flujo de trabajo 

- `main`: versión estable, la que se entrega y se despliega.
- `develop`: integración del trabajo en curso.

