# Entrega 3: microservicio Node.js, Swagger, IA y Compose — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un microservicio Node.js que genera subtareas con Gemini, consumido por Django, con Swagger público, Docker Compose y despliegue.

**Architecture:** Django (`web`) llama por HTTP síncrono a un servicio Express (`sugerencias`), que llama a la API REST de Gemini. Las sugerencias no se guardan; el usuario marca las que quiere y Django crea una `Tarea` por cada una. Dos servicios web independientes en el despliegue.

**Tech Stack:** Python 3.12 / Django 6.1.1 (`urllib` de la librería estándar), Node 20, Express, `swagger-ui-express`, `yaml`, Jest, Supertest, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-11-18-entrega3-microservicio-ia-design.md`

## Global Constraints

- Textos de interfaz, errores y mensajes en **español**.
- Sin modelo `Subtarea` ni migraciones nuevas; las sugerencias se crean como `Tarea`.
- Django sin dependencias nuevas de Python para llamar a Node: usar `urllib`.
- `GEMINI_API_KEY` solo existe en el servicio Node (entorno); nunca en el repo, en imágenes, en Django ni en el navegador.
- `POST /api/sugerencias` exige cabecera `X-API-Key` igual a `INTERNAL_API_KEY`. `GET /health` y `GET /api-docs` son públicos.
- Entrada del endpoint: `titulo` obligatorio (máx. 100), `descripcion` opcional (máx. 1000). Salida: entre 3 y 6 subtareas, cada una de máx. 100 caracteres.
- Errores de Node con cuerpo `{ "error": "mensaje en español" }`: 400 entrada inválida, 401 clave incorrecta, 502 fallo de Gemini.
- Tiempo límite de Django hacia Node: `SUGERENCIAS_TIMEOUT`, por defecto 30 s (el plan gratuito de Render tarda en despertar).
- Todas las vistas nuevas con `@login_required` y solo para el propietario de la tarea (`_tarea_del_usuario`, 404 si es ajena).
- Docker de producción: gunicorn + WhiteNoise + usuario sin privilegios; `requirements.txt` fija `Django==6.1.1`.

## Review Focus

- `titulo` solo con espacios o vacío → 400 en Node; en Django el formulario no envía nada vacío.
- Gemini devuelve JSON válido pero con más de 6 ítems, ítems vacíos o de más de 100 caracteres → Node recorta, limpia y descarta vacíos.
- Gemini devuelve texto que no es JSON, 429 o 5xx → Node responde 502 (no 500).
- Node apagado o sin red (conexión rechazada, tiempo agotado) → Django muestra aviso y la página de detalle sigue cargando.
- Un usuario intenta pedir o agregar sugerencias de una tarea ajena → 404 y no se crea nada.
- `GET` a las rutas de sugerencias → 405.
- Títulos enviados desde el formulario vacíos, de más de 100 caracteres o más de 6 → se descartan, recortan o limitan sin error 500.
- Falta `X-API-Key` o es incorrecta → 401 sin llamar a Gemini.

---

## File Structure

| Archivo | Responsabilidad |
|---|---|
| `microservicio/package.json` | Dependencias y scripts `start` y `test`. |
| `microservicio/src/gemini.js` | Cliente de Gemini: arma la petición y valida/limpia la respuesta. |
| `microservicio/src/app.js` | Express: rutas, validación, autenticación por clave, Swagger. |
| `microservicio/src/server.js` | Arranque del servidor (lee `PORT`). |
| `microservicio/openapi.yaml` | Especificación OpenAPI 3. |
| `microservicio/tests/*.test.js` | Pruebas de `gemini.js`, `app.js` y Swagger. |
| `microservicio/Dockerfile`, `.dockerignore` | Imagen del microservicio. |
| `MyTask/sugerencias.py` | Cliente HTTP de Django hacia Node. |
| `MyTask/views.py`, `MyTask/urls.py` | Vistas `sugerir_subtareas` y `agregar_sugerencias`. |
| `MyTask/templates/MyTask/detalle.html` | Botón y formulario de sugerencias. |
| `MyTask/tests.py` | Pruebas de las vistas y del cliente. |
| `Dockerfile`, `requirements.txt`, `docker-compose.yml`, `.env.example` | Docker de Django fusionado y Compose. |
| `docs/despliegue.md`, `README.md`, `docs/*` | Guía de despliegue y documentación. |

---

### Task 1: Integrar el remoto y fusionar el Docker de Django

**Files:**
- Modify: `Dockerfile`, `requirements.txt`, `.dockerignore`, `README.md` (sección Docker)

**Interfaces:**
- Produces: imagen de Django lista para producción que escucha en el puerto 8000 y toma su configuración de variables `DJANGO_*`.

- [ ] **Step 1: Commit local de los cambios de la Entrega 2** (`settings.py`, `Dockerfile`, `.dockerignore`, `requirements.txt`, `docs/`) y ejecutar `git pull --rebase origin main`. Resolver conflictos en `Dockerfile`, `.dockerignore` y `requirements.txt` conservando el contenido descrito en los pasos 2 y 3.
- [ ] **Step 2: `requirements.txt`** con `Django==6.1.1`, `gunicorn>=23.0`, `whitenoise>=6.9`.
- [ ] **Step 3: `Dockerfile`** de producción (python:3.12-slim, `collectstatic`, usuario `appuser`, `/data` para SQLite, arranque con `migrate` y `gunicorn mysite.wsgi:application --bind 0.0.0.0:8000`). Agregar al `.dockerignore` las entradas de la rama remota que falten y `microservicio/node_modules`.
- [ ] **Step 4: README**: en "Ejecutarlo con Docker" reemplazar el `docker run` por el que monta el volumen `/data` y pasa `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_DB_PATH`; quitar la nota de que SQLite se pierde.
- [ ] **Step 5: Verificar** `python manage.py test` → todas las pruebas existentes pasan (26).
- [ ] **Step 6: Commit** `fix: fusiona Dockerfile de produccion con la rama remota`.

---

### Task 2: Cliente de Gemini en Node

**Files:**
- Create: `microservicio/package.json`, `microservicio/src/gemini.js`, `microservicio/tests/gemini.test.js`

**Interfaces:**
- Produces: `generarSubtareas({ titulo, descripcion }, { apiKey, model, fetchImpl }) → Promise<string[]>` y `class IAError extends Error` exportados de `gemini.js`.

- [ ] **Step 1: `package.json`** (`"type": "commonjs"`, scripts `start: node src/server.js`, `test: jest`; dependencias `express`, `swagger-ui-express`, `yaml`; dev `jest`, `supertest`).
- [ ] **Step 2: Escribir pruebas** en `gemini.test.js` con `fetchImpl` simulado:
  - `devuelve la lista de subtareas cuando Gemini responde JSON valido` → respuesta `{ candidates: [{ content: { parts: [{ text: '{"subtareas":["a","b","c"]}' }] } }] }` produce `['a','b','c']`.
  - `recorta a 6 elementos, a 100 caracteres y descarta vacios` (entrada con 8 ítems, uno vacío y uno de 150 caracteres).
  - `lanza IAError si Gemini responde 429` y `si responde 500`.
  - `lanza IAError si el texto no es JSON` y `si el JSON no trae subtareas`.
  - `lanza IAError si quedan menos de 3 subtareas utiles`.
  - `envia la clave en la cabecera x-goog-api-key y no en la URL`.
- [ ] **Step 3: Ejecutar** `npm test` en `microservicio/` → falla (módulo inexistente).
- [ ] **Step 4: Implementar `generarSubtareas`**: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` con `fetchImpl` (por defecto el `fetch` global de Node 20), cabecera `x-goog-api-key`, prompt en español pidiendo 3 a 6 pasos concretos y cortos para la tarea, y `generationConfig` con `responseMimeType: "application/json"` y un `responseSchema` de `{ subtareas: [string] }`. Cualquier fallo de red, estado no 2xx o contenido inutilizable lanza `IAError`. **Antes de fijar el modelo por defecto, verificar en la documentación vigente de Gemini el nombre de un modelo Flash gratuito y el formato de `responseSchema`.**
- [ ] **Step 5: Ejecutar** `npm test` → pasan.
- [ ] **Step 6: Commit** `feat(microservicio): cliente de Gemini con validacion de respuesta`.

---

### Task 3: API Express con autenticación y validación

**Files:**
- Create: `microservicio/src/app.js`, `microservicio/src/server.js`, `microservicio/tests/app.test.js`

**Interfaces:**
- Consumes: `generarSubtareas` e `IAError` de `gemini.js`.
- Produces: `crearApp({ generar, internalApiKey, openapiPath }) → express.Application` (`generar` por defecto llama a Gemini con `GEMINI_API_KEY` y `GEMINI_MODEL`).

- [ ] **Step 1: Escribir pruebas** con Supertest y `generar` falso:
  - `GET /health` → 200 `{ estado: 'ok' }` sin clave.
  - `POST /api/sugerencias` sin `X-API-Key` → 401 con `error`; con clave incorrecta → 401; `generar` no se llama.
  - Con clave y `{ titulo: 'Estudiar' }` → 200 `{ tarea: 'Estudiar', subtareas: [...] }`.
  - `titulo` ausente, solo espacios o de 101 caracteres → 400; `descripcion` de 1001 caracteres → 400; cuerpo que no es JSON → 400.
  - Si `generar` lanza `IAError` → 502 con `{ error }` en español; si lanza otro error → 502 también (nunca 500).
  - Un `titulo` con emojis y acentos pasa y llega intacto a `generar`.
- [ ] **Step 2: Ejecutar** `npm test` → fallan.
- [ ] **Step 3: Implementar `crearApp`** en `app.js` y `server.js` (lee `PORT`, por defecto 3000, escucha en `0.0.0.0`). Validar con funciones simples, sin librería. Comparar `X-API-Key` en tiempo constante (`crypto.timingSafeEqual`). Si `INTERNAL_API_KEY` no está definida, el servidor no arranca.
- [ ] **Step 4: Ejecutar** `npm test` → pasan.
- [ ] **Step 5: Commit** `feat(microservicio): endpoint POST /api/sugerencias y /health`.

---

### Task 4: Swagger / OpenAPI

**Files:**
- Create: `microservicio/openapi.yaml`, `microservicio/tests/docs.test.js`
- Modify: `microservicio/src/app.js`

**Interfaces:**
- Consumes: `crearApp` de la Task 3.
- Produces: `GET /api-docs` (Swagger UI) y `GET /openapi.yaml`, públicos.

- [ ] **Step 1: Escribir pruebas**: `GET /api-docs/` → 200 con `text/html`; `GET /openapi.yaml` → 200; el YAML parseado con `yaml` tiene `openapi` que empieza por `3.`, define `/health` y `/api/sugerencias` (método `post`), el esquema de seguridad `ApiKeyAuth` (cabecera `X-API-Key`) y las respuestas 200, 400, 401 y 502 de `/api/sugerencias`.
- [ ] **Step 2: Ejecutar** `npm test` → fallan.
- [ ] **Step 3: Escribir `openapi.yaml`** en español, con ejemplos de entrada y salida y los códigos de error de las Global Constraints. Montar `swagger-ui-express` en `/api-docs` con `server.url` relativo (`/`) para que el botón "Try it out" funcione en cualquier dominio.
- [ ] **Step 4: Ejecutar** `npm test` → pasan.
- [ ] **Step 5: Commit** `feat(microservicio): documentacion Swagger en /api-docs`.

---

### Task 5: Cliente HTTP de Django hacia Node

**Files:**
- Create: `MyTask/sugerencias.py`
- Modify: `mysite/settings.py`, `MyTask/tests.py`

**Interfaces:**
- Produces: `pedir_sugerencias(tarea: Tarea) -> list[str]` y `class SugerenciasNoDisponibles(Exception)` (con mensaje en español apto para mostrar al usuario) en `MyTask/sugerencias.py`; ajustes `NODE_SERVICE_URL` (por defecto `http://localhost:3000`), `INTERNAL_API_KEY` (por defecto `''`) y `SUGERENCIAS_TIMEOUT` (por defecto `30`) en `settings.py`, leídos de variables de entorno del mismo nombre.

- [ ] **Step 1: Escribir pruebas** en `MyTask/tests.py` (clase `ClienteSugerenciasTests`), simulando `urllib.request.urlopen` con `unittest.mock.patch`:
  - `test_devuelve_la_lista_de_subtareas` (respuesta 200 con JSON `{"tarea": "x", "subtareas": ["a", "b", "c"]}` → `['a','b','c']`).
  - `test_envia_titulo_descripcion_y_clave` (el `Request` lleva método POST, `Content-Type: application/json`, `X-API-Key` y el cuerpo con título y descripción de la tarea).
  - `test_error_http_del_servicio_lanza_sugerencias_no_disponibles` (502 y 401).
  - `test_servicio_apagado_lanza_sugerencias_no_disponibles` (`URLError`) y `test_tiempo_agotado...` (`TimeoutError`).
  - `test_respuesta_que_no_es_json_lanza_sugerencias_no_disponibles`.
- [ ] **Step 2: Ejecutar** `python manage.py test MyTask.tests.ClienteSugerenciasTests` → falla.
- [ ] **Step 3: Implementar** `pedir_sugerencias` y la excepción; agregar los tres ajustes a `settings.py`.
- [ ] **Step 4: Ejecutar** la clase de pruebas → pasan.
- [ ] **Step 5: Commit** `feat: cliente HTTP de Django hacia el microservicio de sugerencias`.

---

### Task 6: Vistas, URLs y plantilla de sugerencias

**Files:**
- Modify: `MyTask/views.py`, `MyTask/urls.py`, `MyTask/templates/MyTask/detalle.html`, `MyTask/static/MyTask/css/estilos.css` (solo si hace falta), `MyTask/tests.py`

**Interfaces:**
- Consumes: `pedir_sugerencias` y `SugerenciasNoDisponibles` de la Task 5; `_tarea_del_usuario` de `views.py`.
- Produces: URLs `mytask:sugerir_subtareas` (`tarea/<int:tarea_id>/sugerencias/`) y `mytask:agregar_sugerencias` (`tarea/<int:tarea_id>/sugerencias/agregar/`); vistas `sugerir_subtareas(request, tarea_id)` y `agregar_sugerencias(request, tarea_id)`.

- [ ] **Step 1: Escribir pruebas** (clase `SugerenciasViewsTests`, con `pedir_sugerencias` simulado en `MyTask.views`):
  - `test_sugerir_muestra_las_sugerencias_en_el_detalle` (200, contiene cada sugerencia y el botón "Agregar como tareas").
  - `test_sugerir_con_servicio_caido_muestra_aviso_y_la_pagina_carga` (200, contiene el mensaje de error, la bitácora sigue visible).
  - `test_sugerir_tarea_ajena_devuelve_404_y_no_llama_al_servicio`.
  - `test_sugerir_requiere_login` (redirige a `/login/`).
  - `test_sugerir_por_get_devuelve_405` y lo mismo para agregar.
  - `test_agregar_crea_una_tarea_por_cada_titulo_marcado` (propietario = usuario actual, `completada=False`).
  - `test_agregar_recorta_a_100_descarta_vacios_y_limita_a_6` (envía 8 títulos, uno vacío y uno de 150 caracteres).
  - `test_agregar_sin_titulos_no_crea_nada_y_avisa`.
  - `test_agregar_tarea_ajena_devuelve_404_y_no_crea_tareas`.
  - `test_detalle_muestra_el_boton_sugerir_subtareas`.
- [ ] **Step 2: Ejecutar** `python manage.py test MyTask.tests.SugerenciasViewsTests` → fallan.
- [ ] **Step 3: Implementar las vistas** con `@login_required` y `@require_POST`. `sugerir_subtareas` renderiza `detalle.html` con el mismo contexto que `detalle` más `sugerencias`; ante `SugerenciasNoDisponibles` usa `messages.error` con el mensaje de la excepción. `agregar_sugerencias` lee `request.POST.getlist('sugerencia')`, aplica `strip`, descarta vacíos, recorta a 100 y toma los primeros 6, crea las tareas y redirige a `mytask:index` con `messages.success` que indica cuántas se agregaron.
- [ ] **Step 4: Plantilla**: en `detalle.html`, una tarjeta "Subtareas sugeridas por IA" con el botón `🤖 Sugerir subtareas` (formulario POST con CSRF) y, si hay `sugerencias`, un formulario con un checkbox marcado por cada una (`name="sugerencia"`) y el botón "Agregar como tareas". Reutilizar clases CSS existentes.
- [ ] **Step 5: Ejecutar** `python manage.py test` → todas pasan (las 26 anteriores más las nuevas).
- [ ] **Step 6: Commit** `feat: sugerir subtareas con IA desde el detalle de la tarea`.

---

### Task 7: Docker del microservicio y Docker Compose

**Files:**
- Create: `microservicio/Dockerfile`, `microservicio/.dockerignore`, `docker-compose.yml`, `.env.example`
- Modify: `.gitignore` (confirmar que `.env` sigue ignorado)

**Interfaces:**
- Produces: `docker compose up --build` levanta `web` (puerto 8000) y `sugerencias` (puerto 3000).

- [ ] **Step 1: `microservicio/Dockerfile`**: `node:20-alpine`, `npm ci --omit=dev`, copiar `src/` y `openapi.yaml`, `USER node`, `CMD ["node", "src/server.js"]`. `.dockerignore` excluye `node_modules` y `tests`.
- [ ] **Step 2: `docker-compose.yml`**: servicio `sugerencias` (build `./microservicio`, `env_file: .env`, puerto `3000:3000`, healthcheck sobre `/health`) y servicio `web` (build `.`, `env_file: .env`, puerto `8000:8000`, volumen nombrado en `/data`, `NODE_SERVICE_URL=http://sugerencias:3000`, `DJANGO_DB_PATH=/data/db.sqlite3`, `depends_on` con `condition: service_healthy`).
- [ ] **Step 3: `.env.example`** con `GEMINI_API_KEY=`, `GEMINI_MODEL=`, `INTERNAL_API_KEY=`, `DJANGO_SECRET_KEY=`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`, sin valores reales.
- [ ] **Step 4: Verificar** con `docker compose config` (valida la sintaxis; si Docker no está instalado, anotarlo y dejar la prueba real para el equipo con Docker). Con Docker: `docker compose up --build`, abrir `http://localhost:3000/api-docs` y `http://localhost:8000/`, crear una tarea y pedir sugerencias.
- [ ] **Step 5: Commit** `feat: Docker Compose con Django y el microservicio de sugerencias`.

---

### Task 8: Guía de despliegue público

**Files:**
- Create: `docs/despliegue.md`

- [ ] **Step 1: Redactar la guía paso a paso para alguien que nunca desplegó**, en español, con estas decisiones ya tomadas:
  1. Subir el repositorio a GitHub (`git push` de `main`).
  2. Crear cuenta en Render y conectar GitHub. La URL pública (`https://<nombre>.onrender.com`) la asigna Render al crear cada servicio; no hace falta comprar dominio.
  3. Servicio 1, **microservicio**: *New → Web Service*, repositorio, *Root Directory* `microservicio`, *Runtime* Docker, plan Free, variables `GEMINI_API_KEY`, `GEMINI_MODEL`, `INTERNAL_API_KEY`. Resultado: `https://<node>.onrender.com/api-docs`.
  4. Servicio 2, **Django**: *Root Directory* vacío, Docker, variables `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=<django>.onrender.com`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://<django>.onrender.com`, `NODE_SERVICE_URL=https://<node>.onrender.com`, `INTERNAL_API_KEY` (el mismo valor que en Node).
  5. Crear el superusuario desde la consola de Render (*Shell*) o dejar una cuenta de demostración.
  6. Antes de la demo o del video, abrir `/health` del microservicio y la página de Django para despertar los servicios.
  7. Limitaciones a avisar: el plan gratuito duerme tras 15 minutos sin uso (primer llamado lento) y **no tiene disco persistente, así que la base SQLite se reinicia en cada redespliegue**; aceptable para esta entrega, la solución es PostgreSQL (trabajo futuro).
- [ ] **Step 2: Verificar manualmente en la URL pública**: Swagger carga sin iniciar sesión, "Authorize" + "Try it out" devuelve subtareas, y en Django se registra un usuario, se crea una tarea, se piden sugerencias y se agregan.
- [ ] **Step 3: Commit** `docs: guia de despliegue publico en Render`.

---

### Task 9: Documentación actualizada

**Files:**
- Modify: `README.md`, `docs/diagramas_uml.md`, `docs/matriz_trazabilidad.md`
- Create: `docs/SRS_entrega3_actualizacion.md`

- [ ] **Step 1: README**: tabla de estado (Entrega 3), tecnologías (Node.js, Express, Swagger, Gemini, Compose), estructura del repositorio con `microservicio/`, variables de entorno, cómo correr con `docker compose up --build`, URLs pública y de Swagger.
- [ ] **Step 2: `diagramas_uml.md`**: agregar diagrama de componentes (Navegador, Django, Node, Gemini, SQLite), diagrama de despliegue (dos servicios en Render) y secuencia de "sugerir y agregar subtareas" incluyendo el camino de error. Evitar `<<...>>` con puntos en Mermaid; exportar los PNG revisándolos antes de entregarlos.
- [ ] **Step 3: `matriz_trazabilidad.md`**: filas para HU16 a HU21, HU24 y HU28 con archivos reales y nombres de las pruebas de las Tasks 2 a 6; marcar Hecho solo lo verificado.
- [ ] **Step 4: `SRS_entrega3_actualizacion.md`** con la misma estructura del de la Entrega 2 (alcance, tecnologías, UML, backlog con estados, API del microservicio, despliegue, Compose, limitaciones conocidas).
- [ ] **Step 5: Commit** `docs: actualiza README, UML, matriz y SRS para la Entrega 3`.

---

## Self-Review

- **Cobertura del spec:** microservicio y Swagger (Tasks 2 a 4), integración Django (5 y 6), IA (2), clave interna (3), Compose (7), despliegue (8), documentación (9), fusión de Docker (1), aviso ante fallos (5 y 6). Sin brechas.
- **Consistencia de nombres:** `generarSubtareas`/`IAError` (Task 2) usados en Task 3; `crearApp` (Task 3) usado en Task 4; `pedir_sugerencias`/`SugerenciasNoDisponibles` (Task 5) usados en Task 6; URLs de Task 6 usadas en la plantilla.
- **Tiempo límite:** el spec dejaba el valor abierto; el plan fija 30 s por el arranque en frío de Render.
- **Prueba real con Gemini:** ninguna prueba automática usa la clave real; se hace a mano en las Tasks 7 y 8.
