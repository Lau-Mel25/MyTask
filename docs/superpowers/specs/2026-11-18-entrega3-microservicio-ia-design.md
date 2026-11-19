# Entrega 3: microservicio Node.js, Swagger, IA (Gemini) y Docker Compose

Fecha: 2026-11-18 · Entrega: 19/11/2026 · Estado: **pendiente de aprobación**

## Intención

MyTask ya permite gestionar tareas con bitácora, login y roles (Entrega 2). La Entrega 3 agrega la arquitectura del README: `Usuario → Django → Node.js → IA`. Un usuario con una tarea grande pide sugerencias de pasos; la IA propone subtareas y el usuario las agrega con un clic como tareas propias. Es el valor del proyecto: ayudar a empezar tareas que se postergan por no saber por dónde partir.

Entregables del curso: microservicio Node.js funcional y desplegado, Swagger público, integración Django → Node operativa, integración con IA operativa, Docker Compose implementado, documentación actualizada.

## Objetivos, no objetivos y antiobjetivos

**Objetivos**
- `POST /api/sugerencias` en Node devuelve 3 a 6 subtareas generadas por Gemini.
- Swagger/OpenAPI público en `/api-docs` que permite probar los endpoints.
- Botón "Sugerir subtareas" en el detalle de la tarea; cada sugerencia se agrega como `Tarea` del usuario.
- Aviso claro y sin romper la app cuando la IA o Node fallan (HU20).
- `docker compose up` levanta Django y Node con un comando.
- Ambos servicios desplegados en una URL pública.

**No objetivos**
- No hay modelo `Subtarea` ni migración (descartado: opción C).
- No se guardan las sugerencias; si el usuario recarga, vuelve a pedirlas.
- No hay PostgreSQL, colas ni caché; Django sigue con SQLite en volumen.
- No hay historial de uso de la IA ni límites por usuario.

**Antiobjetivos (sería un fracaso aunque funcione)**
- La clave de Gemini en el repositorio, en la imagen Docker, en Django o en el navegador.
- Que una caída de la IA deje la página de la tarea con error 500.
- Que cualquier persona en internet pueda gastar la cuota de Gemini llamando al endpoint público.

## Restricciones

- Gemini en plan gratuito: cuota limitada, puede responder 429. Tratarlo como fallo normal.
- Docker no está instalado en la máquina de desarrollo actual; Compose se probará en otro equipo o en el despliegue.
- Entrega el 19/11: priorizar el flujo completo de punta a punta sobre el pulido.
- Se debe respetar lo existente: Django 6, `login_required`, aislamiento por usuario, textos en español, estilo de `estilos.css`.

## Enfoques considerados

| Opción | Qué hace | Por qué |
|---|---|---|
| A. Solo mostrar | Lista de sugerencias, sin acciones | Descartada: la demo queda pobre y el usuario copia a mano. |
| **B. Mostrar y crear con un clic** | Sugerencias con checkbox y botón "Agregar como tareas"; crea `Tarea` normales | **Elegida por el usuario.** Reutiliza `Tarea`, sin migración, demo completa. |
| C. Modelo `Subtarea` | Subtareas ligadas a cada tarea | Descartada: migración, vistas, plantillas y diagrama nuevos; no cabe en el plazo. |

## Diseño

### Arquitectura

```
Navegador → Django (puerto 8000) → Node.js/Express (puerto 3000) → API de Gemini
                 │
                 └→ SQLite (volumen /data)
```

Docker Compose define dos servicios, `web` (Django) y `sugerencias` (Node). Dentro de Compose, Django llama a `http://sugerencias:3000`. En el despliegue público son dos servicios web separados y Django usa la URL pública de Node.

### Microservicio Node (`microservicio/`)

Express con `swagger-ui-express` y una especificación OpenAPI 3 en `openapi.yaml`.

| Método y ruta | Descripción |
|---|---|
| `GET /health` | Estado del servicio, sin autenticación. |
| `GET /api-docs` | Swagger UI público. |
| `POST /api/sugerencias` | Genera subtareas. Requiere cabecera `X-API-Key`. |

`POST /api/sugerencias`

- Entrada: `{ "titulo": string (obligatorio, máx. 100), "descripcion": string (opcional, máx. 1000) }`
- Salida 200: `{ "tarea": string, "subtareas": [string] }`, entre 3 y 6 elementos, cada uno de máx. 100 caracteres.
- 400: entrada inválida. 401: falta o es incorrecta la `X-API-Key`. 502: Gemini falló, respondió algo inutilizable o devolvió 429. Cuerpo de error siempre `{ "error": "mensaje en español" }`.
- Gemini se llama desde Node con la clave en `GEMINI_API_KEY`. El prompt pide una lista de pasos concretos y cortos en español, y la respuesta se pide en JSON estructurado; Node valida y recorta el resultado antes de devolverlo.
- La `X-API-Key` de Swagger se declara como esquema de seguridad, de modo que "Authorize" permite probar el endpoint en la demo.

Variables de entorno: `GEMINI_API_KEY`, `INTERNAL_API_KEY`, `GEMINI_MODEL` (por defecto un modelo Flash gratuito vigente), `PORT`.

### Django

- `NODE_SERVICE_URL` e `INTERNAL_API_KEY` en `settings.py` desde variables de entorno.
- Módulo `MyTask/sugerencias.py` con una función `pedir_sugerencias(tarea)` que hace la llamada HTTP con `urllib` (sin dependencias nuevas), tiempo límite de 15 s, y convierte cualquier fallo en una excepción propia `SugerenciasNoDisponibles`.
- `POST /myTask/tarea/<id>/sugerencias/` (`login_required`, solo el propietario): llama al servicio y renderiza `detalle.html` con la lista de sugerencias. Si falla, muestra un `messages.error` claro y la página sigue normal.
- `POST /myTask/tarea/<id>/sugerencias/agregar/` (`login_required`, solo el propietario): recibe los títulos marcados, los recorta a 100 caracteres, descarta vacíos, máximo 6, y crea una `Tarea` por cada uno con `propietario=request.user`.
- `detalle.html`: botón "Sugerir subtareas" y, cuando hay sugerencias, un formulario con checkboxes y "Agregar como tareas".

### Docker y Compose

- Se fusionan los Dockerfile de Django: el del repositorio (commit `e493661`, con `runserver`) y el de la Entrega 2 (gunicorn, WhiteNoise, usuario sin privilegios). Se conserva la versión de producción y se documenta en el README.
- `microservicio/Dockerfile`: `node:20-alpine`, `npm ci --omit=dev`, usuario sin privilegios.
- `docker-compose.yml`: servicios `web` y `sugerencias`, volumen para `/data`, red interna, `env_file: .env`, `depends_on`. Se agrega `.env.example` con todas las variables sin valores reales. `.env` ya está en `.gitignore`.

### Despliegue

Dos servicios web separados (plataforma sugerida: Render, plan gratuito), cada uno construido desde su Dockerfile, con sus variables de entorno cargadas en el panel de la plataforma. Swagger queda en `https://<servicio-node>/api-docs`.

### Pruebas

- Node: Jest y Supertest con Gemini simulado (200, 400, 401, 502 y respuesta mal formada).
- Django: pruebas con la llamada HTTP simulada (éxito, fallo del servicio, propietario ajeno recibe 404, creación de tareas desde sugerencias con recorte y límite de 6).
- Prueba manual de punta a punta con la clave real de Gemini.

### Documentación

README, SRS (alcance, tecnologías, componentes, despliegue, backlog HU16 a HU21 y HU24, HU28), matriz de trazabilidad y diagramas actualizados: componentes con el microservicio, despliegue con dos servicios y secuencia de "sugerir subtareas".

## Decisiones tomadas por mí (corrígelas si no te convienen)

- **`X-API-Key` entre Django y Node:** no lo pediste, pero Node es público para que Swagger funcione y sin esto cualquiera gastaría tu cuota de Gemini.
- **`urllib` en vez de `requests`:** evita una dependencia nueva en Django.
- **Express y Jest:** opciones estándar y fáciles de explicar en la sustentación.
- **Render como plataforma:** tiene plan gratuito y despliega desde Dockerfile; si el curso exige otra, solo cambia esta sección.
- **Sugerencias sin persistir:** simplifica el diseño; recargar la página las pierde.

## Pendiente para quien construya

- Elegir el nombre exacto del modelo de Gemini y su formato de salida JSON verificando la documentación vigente de la API.
- Redactar el prompt y ajustarlo con pruebas reales.
- Decidir el tiempo de espera del arranque en frío del plan gratuito (el primer llamado puede tardar).

## Qué necesito de ti

- Una clave de Gemini (Google AI Studio), que pondrás tú en `.env` y en el panel de despliegue. Yo nunca la veo ni la guardo.
- Confirmar la plataforma de despliegue permitida por el curso.
