# Diagramas UML — MyTask

Los diagramas están en Mermaid. Se ven directamente en GitHub y en VS Code (extensión *Markdown Preview Mermaid Support*). Para pegarlos en el SRS, ábrelos en <https://mermaid.live> y exporta PNG o SVG. Los PNG ya exportados están en esta carpeta.

## 1. Diagrama de clases (modelos)

`User` es el modelo de autenticación de Django (`django.contrib.auth`); las otras tres clases están en `MyTask/models.py`. Imagen: `diagrama_clases_modelos.png`.

```mermaid
classDiagram
    direction LR

    class User {
        <<Django>>
        +int id
        +str username
        +str password
        +str email
        +bool is_staff
        +bool is_superuser
    }

    class Perfil {
        +int id
        +str rol
        +es_administrador() bool
        +save()
    }

    class Rol {
        <<enumeration>>
        USUARIO
        ADMINISTRADOR
    }

    class Tarea {
        +int id
        +str titulo
        +str descripcion
        +datetime fecha_creacion
        +bool completada
    }

    class Registro {
        +int id
        +str detalle
        +datetime fecha
    }

    User "1" -- "1" Perfil : perfil
    Perfil ..> Rol : usa
    User "1" -- "0..*" Tarea : propietario / tareas
    Tarea "1" *-- "0..*" Registro : registros
```

**Reglas de negocio reflejadas en el modelo**

- Un `Perfil` se crea automáticamente al registrar un `User` (señal `post_save`). Los superusuarios nacen como Administrador.
- Al guardar un `Perfil`, el campo `is_staff` del usuario se sincroniza con el rol para dar o quitar acceso a Django Admin.
- Eliminar un `User` elimina su `Perfil` y sus `Tarea` (`CASCADE`); eliminar una `Tarea` elimina sus `Registro`.

## 2. Diagrama de secuencia (primera versión): crear una tarea con sesión iniciada

```mermaid
sequenceDiagram
    actor U as Usuario
    participant N as Navegador
    participant D as Django (views / forms)
    participant A as Auth (sesión)
    participant DB as Base de datos (SQLite)

    U->>N: Abre /myTask/nueva/
    N->>D: GET /myTask/nueva/
    D->>A: ¿Hay sesión válida? (login_required)
    alt Sin sesión
        A-->>D: No autenticado
        D-->>N: Redirige a /login/
        U->>N: Ingresa usuario y contraseña
        N->>D: POST /login/
        D->>DB: Verifica credenciales
        DB-->>D: Usuario válido
        D-->>N: Crea sesión y redirige a /myTask/
    else Con sesión
        A-->>D: Usuario autenticado
        D-->>N: Formulario de nueva tarea
    end
    U->>N: Escribe título y descripción
    N->>D: POST /myTask/nueva/
    D->>D: Valida el formulario
    D->>DB: INSERT Tarea (propietario = usuario actual)
    DB-->>D: Tarea creada
    D-->>N: Redirige a /myTask/
    N->>D: GET /myTask/
    D->>DB: SELECT tareas WHERE propietario = usuario actual
    DB-->>D: Lista de tareas
    D-->>N: Página con pendientes y completadas
    N-->>U: Muestra la nueva tarea
```

## 3. Diagrama de componentes (Entrega 3)

```mermaid
flowchart LR
    U([Usuario]) --> N[Navegador]
    N -->|HTTPS| D["Django: vistas, roles y Django Admin"]
    D -->|SQL| DB[(SQLite)]
    D -->|"HTTP con X-API-Key"| M["Microservicio Node.js: Express y Swagger"]
    N -->|"/api-docs"| M
    M -->|"HTTPS con clave de Gemini"| G[API de Gemini]
```

## 4. Diagrama de despliegue (Entrega 3)

Con Docker Compose en un computador local son los mismos dos contenedores (`web` y `sugerencias`); en el despliegue público son dos servicios web de Render.

```mermaid
flowchart TB
    B[Navegador del usuario]
    DJ["Render - servicio web mytask<br/>Contenedor Docker: Gunicorn, Django y WhiteNoise"]
    FS[("SQLite en disco efimero")]
    ND["Render - servicio web mytask-sugerencias<br/>Contenedor Docker: Node.js, Express y Swagger"]
    GE["API de Gemini - Google"]
    B -->|HTTPS| DJ
    B -->|"HTTPS /api-docs"| ND
    DJ --> FS
    DJ -->|"HTTPS con X-API-Key"| ND
    ND -->|HTTPS| GE
```

## 5. Diagrama de secuencia: sugerir y agregar subtareas (Entrega 3)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant N as Navegador
    participant D as Django
    participant M as Microservicio Node
    participant G as Gemini

    U->>N: Pulsa Sugerir subtareas
    N->>D: POST sugerencias de la tarea
    D->>D: Verifica sesion y que la tarea sea suya
    D->>M: POST /api/sugerencias con X-API-Key
    M->>M: Valida la clave y los datos
    M->>G: generateContent con titulo y descripcion
    alt La IA responde bien
        G-->>M: JSON con subtareas
        M-->>D: 200 con 3 a 6 subtareas
        D-->>N: Detalle con las sugerencias marcadas
        U->>N: Pulsa Agregar como tareas
        N->>D: POST agregar sugerencias
        D->>D: Crea una Tarea por cada sugerencia
        D-->>N: Redirige a la lista de tareas
    else Falla la IA o el servicio
        G-->>M: Error o limite de uso
        M-->>D: 502 con mensaje en espanol
        D-->>N: Detalle con aviso de error
    end
```
