# MyTask — SRS, Entrega 3 (texto actualizado)

> Mantiene la estructura, numeración y tablas del SRS anterior. Solo cambia lo marcado como **[CAMBIA]** o **[NUEVO]**. Pega cada bloque en su sección del documento original para conservar el formato.

---

## Portada

| | |
|---|---|
| **Subtítulo** **[CAMBIA]** | Entrega 3: microservicio Node.js, Swagger, IA generativa y Docker Compose |
| **Entrega** **[CAMBIA]** | Entrega 3: integración de microservicios e IA |
| **Despliegue** | Aplicación: [pegar URL de Django] · Swagger: [pegar URL de Node]/api-docs |

---

## 1. Introducción

### 1.4 Alcance **[CAMBIA]**

Incluye (estado a la Entrega 3):

- Gestión de tareas con bitácora de avances, autenticación, roles y Django Admin. *(Entrega 2)*
- Microservicio Node.js con API REST, documentada con Swagger/OpenAPI. **(Implementado)**
- Integración Django → Node.js. **(Implementada)**
- Sugerencia de subtareas con IA generativa (Gemini), que el usuario agrega como tareas propias. **(Implementada)**
- Dockerfile, Docker Compose y despliegue en la nube. **(Dockerfile y Compose implementados; despliegue público según `docs/despliegue.md`)**

### 1.5 Tecnologías **[CAMBIA]**

| Componente | Tecnología | Función |
|---|---|---|
| Aplicación web | Python y Django | Vistas, plantillas, modelos, autenticación, roles y Django Admin. |
| Servidor de aplicación | Gunicorn y WhiteNoise | Ejecutan Django en el contenedor y sirven los archivos estáticos. |
| Microservicio | Node.js y Express | API REST independiente que genera las sugerencias. |
| IA generativa | API de Gemini (Google) | Genera de 3 a 6 subtareas a partir del título y la descripción de una tarea. |
| Base de datos | SQLite (volumen en Docker; disco efímero en el plan gratuito de Render) | Persistencia de usuarios, tareas y registros. PostgreSQL queda como mejora futura. |
| Contenedores | Docker y Docker Compose | Una imagen por servicio; Compose levanta ambos con un comando. |
| Documentación de API | Swagger / OpenAPI 3 (`swagger-ui-express`) | Documenta y permite probar los endpoints en `/api-docs`. |
| Pruebas | Django `TestCase`; Jest y Supertest | 44 pruebas en Django y 32 en el microservicio. |
| Control de versiones | GitHub | Repositorio, ramas y seguimiento de cambios. |

### 1.6 Actores
Sin cambios. El **Servicio de IA (externo)** es ahora la API de Gemini, consumida únicamente por el microservicio Node.js.

---

## 2. Diagramas UML

### 2.1 Casos de uso **[CAMBIA]**
Agregar al caso de uso del Usuario: **Sugerir subtareas con IA** (extiende *Ver detalle de una tarea*) y **Agregar sugerencias como tareas**.

### 2.2 Componentes **[CAMBIA]**
Insertar `docs/diagrama_componentes.png`: Navegador → Django (vistas, roles, Django Admin) → SQLite; Django → Microservicio Node.js (HTTP con `X-API-Key`) → API de Gemini. El navegador también consulta `/api-docs` del microservicio.

### 2.3 Despliegue **[CAMBIA]**
Insertar `docs/diagrama_despliegue.png`: dos servicios web (Django y microservicio), cada uno en su contenedor Docker; Django guarda en SQLite; Node llama a Gemini por HTTPS.

### 2.4 Diagrama de clases (modelos)
Sin cambios. No se agregaron modelos: las sugerencias se crean como `Tarea` normales.

### 2.5 Diagrama de secuencia **[CAMBIA]**
Insertar `docs/diagrama_secuencia_sugerencias.png` (sugerir y agregar subtareas, con el camino de error de la IA).

---

## 3. Backlog (Historias de usuario) **[CAMBIA: estado]**

Solo cambian las historias de la Entrega 3 (las anteriores quedan como en la Entrega 2).

| ID | Historia de usuario | Prioridad | Entrega | Estado |
|---|---|---|---|---|
| HU16 | Como equipo, queremos un microservicio Node.js con API REST. | Alta | 3 | En curso (falta publicar) |
| HU17 | Como desarrollador, quiero Swagger público para probar los endpoints. | Alta | 3 | En curso (falta URL pública) |
| HU18 | Como equipo, queremos que Django consuma el microservicio. | Alta | 3 | **Hecho** |
| HU19 | Como usuario, quiero que la IA me sugiera subtareas. | Alta | 3 | En curso (falta prueba real con Gemini) |
| HU21 | Como equipo, queremos Docker Compose para levantar todo con un comando. | Alta | 3 | En curso (falta probar con Docker) |
| HU20 | Como usuario, quiero un aviso claro si la IA falla. | Alta | 3 | **Hecho** |
| HU28 | Como equipo, queremos actualizar el SRS, el UML y la matriz, y grabar el Video 3. | Alta | 3 | En curso (falta el video) |
| HU24 | Como equipo, queremos README profesional y pruebas automáticas básicas. | Alta | 3 | **Hecho** |
| HU29 | Como equipo, queremos el despliegue final, el video final y la preparación de la sustentación. | Alta | 3 | Pendiente |

---

## 4. Microservicio de sugerencias **[NUEVO]**

| Método y ruta | Autenticación | Descripción |
|---|---|---|
| `GET /health` | No | Estado del servicio. |
| `GET /api-docs` | No | Swagger UI. |
| `GET /openapi.yaml` | No | Especificación OpenAPI. |
| `POST /api/sugerencias` | Cabecera `X-API-Key` | Genera subtareas. |

**Entrada:** `{ "titulo": string (obligatorio, máx. 100), "descripcion": string (opcional, máx. 1000) }`
**Salida 200:** `{ "tarea": string, "subtareas": [string] }`, de 3 a 6 elementos de máximo 100 caracteres.

| Código | Cuándo | Cuerpo |
|---|---|---|
| 400 | Entrada inválida o JSON mal formado | `{ "error": "mensaje en español" }` |
| 401 | Falta la clave o es incorrecta | `{ "error": "..." }` |
| 502 | La IA falló, alcanzó su límite o devolvió algo inutilizable | `{ "error": "..." }` |

**Decisiones de diseño**

- La clave de Gemini (`GEMINI_API_KEY`) existe solo en el microservicio; Django solo conoce la clave interna `INTERNAL_API_KEY`, que protege el endpoint público y evita que terceros consuman la cuota de Gemini.
- Django llama con un tiempo límite de 30 s (`SUGERENCIAS_TIMEOUT`) y, si el servicio falla, muestra un aviso sin romper la página (HU20).
- Las sugerencias no se guardan; el usuario marca las que quiere y se crean como `Tarea` (máximo 6, título de hasta 100 caracteres).

## 5. Docker, Compose y despliegue **[CAMBIA]**

- **Dockerfile de Django:** `python:3.12-slim`, Gunicorn, WhiteNoise, usuario sin privilegios; al arrancar aplica migraciones y, si existen `DJANGO_SUPERUSER_*`, crea el administrador.
- **Dockerfile del microservicio:** `node:20-alpine`, `npm ci --omit=dev`, usuario `node`.
- **`docker-compose.yml`:** servicios `sugerencias` (puerto 3000) y `web` (puerto 8000), volumen `datos` para la base SQLite y variables tomadas de `.env` (plantilla en `.env.example`).
- **Despliegue:** dos servicios web en Render (plan gratuito) construidos desde sus Dockerfile. Guía en `docs/despliegue.md`.

**Limitaciones conocidas**

- En el plan gratuito de Render los servicios se duermen tras unos 15 minutos y el primer acceso es lento.
- Sin disco persistente, la base SQLite se reinicia en cada despliegue (mejora futura: PostgreSQL).
- Las pruebas automáticas simulan a Gemini; la integración real se verifica manualmente.

## 6. Matriz de trazabilidad **[CAMBIA]**

Pegar la tabla de `docs/matriz_trazabilidad.md` (secciones 1 a 4 de la Entrega 2 y sección 6 de la Entrega 3).
