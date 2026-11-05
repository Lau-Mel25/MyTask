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
| 2 | 12/11/2026 | CRUD, login, roles, Django Admin, Docker y despliegue inicial | Pendiente |
| 3 | 19/11/2026 | Microservicio Node.js, Swagger, IA, Docker Compose | Pendiente |
| Final | 26/11/2026 | Sustentación | Pendiente |

### Funcionalidades actuales (app `MyTask`)

- Crear tareas con título y descripción.
- Listar tareas pendientes y completadas.
- Ver el detalle de una tarea y su bitácora.
- Editar y eliminar tareas.
- Marcar una tarea como completada o pendiente.
- Registrar avances en la bitácora de cada tarea.

### Funcionalidades planeadas

- Registro, inicio de sesión y roles (usuario y administrador).
- Microservicio en Node.js con API REST documentada con Swagger/OpenAPI.
- Sugerencia de subtareas con IA generativa.
- Contenedores con Docker y Docker Compose.

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
├── mysite/        # configuración del proyecto Django
├── MyTask/        # app del gestor de tareas (modelos, vistas, plantillas)
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

La aplicación queda en `http://127.0.0.1:8000/myTask/` y el panel de administración en `http://127.0.0.1:8000/admin/`.

## Flujo de trabajo 

- `main`: versión estable, la que se entrega y se despliega.
- `develop`: integración del trabajo en curso.

