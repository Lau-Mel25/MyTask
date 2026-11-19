# Guía de despliegue (versión básica)

Esta guía es para quien nunca ha desplegado una aplicación. Hay dos partes:

- **Parte A (opcional):** probar todo en tu computador con Docker.
- **Parte B:** publicar la aplicación en internet con **Render**. Render te da una URL pública gratis (como `https://mytask-sugerencias.onrender.com`); no necesitas comprar ni configurar nada.

> Los nombres de los botones de Render pueden cambiar un poco con el tiempo. Si algo no coincide, busca el botón parecido.

## Antes de empezar

1. **Clave de Gemini (gratis):** entra a <https://aistudio.google.com>, inicia sesión con tu cuenta de Google y pulsa **Get API key**. Copia la clave y guárdala; no la compartas ni la pegues en el código.
2. **Dos claves inventadas por ti** (cualquier texto largo y difícil de adivinar). Sirven para `INTERNAL_API_KEY` y `DJANGO_SECRET_KEY`. Si quieres generarlas, ejecuta esto dos veces en una terminal:

   ```bash
   node -e "console.log(require('crypto').randomBytes(24).toString('hex'))"
   ```

3. **El código en GitHub.** Render lee tu repositorio, así que los cambios deben estar subidos y mezclados en `main`:

   ```bash
   git push origin entrega-3
   ```

   Luego abre un Pull Request de `entrega-3` hacia `main` en GitHub y mézclalo (*Merge*).

---

## Parte A (opcional): probarlo en tu computador

Necesitas **Docker Desktop** instalado y abierto (el ícono de la ballena debe decir que está corriendo).

1. En la carpeta del proyecto, copia el archivo de ejemplo:

   ```bash
   copy .env.example .env
   ```

2. Abre `.env` con el Bloc de notas y completa `GEMINI_API_KEY`, `INTERNAL_API_KEY`, `DJANGO_SECRET_KEY` y la contraseña del administrador (`DJANGO_SUPERUSER_PASSWORD`).
3. Levanta todo con un comando (la primera vez tarda unos minutos):

   ```bash
   docker compose up --build
   ```

4. Abre:
   - La aplicación: <http://localhost:8000>
   - Swagger: <http://localhost:3000/api-docs>
5. Para apagar todo, pulsa `Ctrl + C` en esa terminal.

---

## Parte B: publicar en Render

Vas a crear **dos servicios**: primero el microservicio (Node) y después Django, porque Django necesita saber la URL de Node.

### Paso 1. Crear la cuenta

Entra a <https://render.com>, pulsa **Get Started** e inicia sesión **con GitHub**. Autoriza a Render para ver tu repositorio.

### Paso 2. Servicio 1: el microservicio (Node)

1. Pulsa **New +** → **Web Service** → **Build and deploy from a Git repository** → elige tu repositorio → **Connect**.
2. Completa:

   | Campo | Valor |
   |---|---|
   | Name | `mytask-sugerencias` (o el nombre que quieras) |
   | Branch | `main` |
   | Root Directory | `microservicio` |
   | Language / Runtime | `Docker` |
   | Instance Type | `Free` |

3. En **Environment Variables** agrega:

   | Variable | Valor |
   |---|---|
   | `GEMINI_API_KEY` | tu clave de Gemini |
   | `GEMINI_MODEL` | `gemini-3.5-flash-lite` |
   | `INTERNAL_API_KEY` | tu clave inventada (anótala, la usarás otra vez) |

4. Pulsa **Create Web Service** y espera a que el estado diga **Live** (unos minutos).
5. Arriba verás tu URL, por ejemplo `https://mytask-sugerencias.onrender.com`. **Cópiala.**
6. Compruébalo en el navegador:
   - `https://<tu-url>/health` debe mostrar `{"estado":"ok"}`.
   - `https://<tu-url>/api-docs` es **tu Swagger público**.

### Paso 3. Servicio 2: Django

1. **New +** → **Web Service** → mismo repositorio → **Connect**.
2. Completa:

   | Campo | Valor |
   |---|---|
   | Name | `mytask` (o el que quieras) |
   | Branch | `main` |
   | Root Directory | *(déjalo vacío)* |
   | Language / Runtime | `Docker` |
   | Instance Type | `Free` |

3. **Environment Variables:**

   | Variable | Valor |
   |---|---|
   | `DJANGO_SECRET_KEY` | tu otra clave inventada |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
   | `NODE_SERVICE_URL` | la URL del Paso 2, sin `/` al final |
   | `INTERNAL_API_KEY` | **exactamente la misma** del Paso 2 |
   | `DJANGO_SUPERUSER_USERNAME` | `admin` |
   | `DJANGO_SUPERUSER_PASSWORD` | una contraseña tuya |
   | `DJANGO_SUPERUSER_EMAIL` | cualquier correo |

4. **Create Web Service** y espera a **Live**. Esa URL es **tu aplicación pública**.

### Paso 4. Probar de punta a punta

1. Abre la URL de Django, regístrate, crea una tarea y entra a su detalle.
2. Pulsa **Sugerir subtareas**, marca las que quieras y pulsa **Agregar como tareas**.
3. Abre el Swagger, entra a `POST /api/sugerencias`, pulsa **Try it out** y pega tu `INTERNAL_API_KEY` en el campo **X-API-Key** (también puedes usar **Authorize**). Luego pulsa **Execute**.
4. Entra a `/admin/` con el usuario `admin` para mostrar el rol de administrador.

---

## Cosas que debes saber (limitaciones del plan gratuito)

- **Se duermen.** Tras unos 15 minutos sin visitas, los servicios se apagan y el primer acceso tarda cerca de un minuto. **Antes de grabar el video o sustentar**, abre `/health` del microservicio y la página de Django para despertarlos.
- **Los datos se borran.** Render gratis no guarda archivos entre despliegues, así que la base SQLite se reinicia cada vez que se vuelve a desplegar. El administrador se vuelve a crear solo; los demás usuarios y tareas hay que registrarlos de nuevo. La solución definitiva sería PostgreSQL (trabajo futuro).
- **Si la IA falla:** la aplicación muestra un aviso y sigue funcionando. Puede pasar si se agotó el límite gratuito de Gemini; espera un momento e inténtalo de nuevo.
- **Seguridad:** `DJANGO_ALLOWED_HOSTS=.onrender.com` acepta cualquier subdominio de Render; es suficiente para esta entrega.

## Si algo falla

| Síntoma | Qué revisar |
|---|---|
| El servicio queda en "Failed" | En Render, pestaña **Logs**: el último mensaje dice qué faltó (casi siempre una variable de entorno). |
| Django muestra "Bad Request (400)" | `DJANGO_ALLOWED_HOSTS` mal escrito. Debe ser `.onrender.com`. |
| "Verificación CSRF fallida" al iniciar sesión | `DJANGO_CSRF_TRUSTED_ORIGINS` debe ser `https://*.onrender.com`. |
| Las sugerencias dicen "No se pudo conectar" | `NODE_SERVICE_URL` incorrecta, o Node dormido: abre su `/health` y espera. |
| Las sugerencias dicen "no está disponible" | `INTERNAL_API_KEY` distinta en los dos servicios, o `GEMINI_API_KEY` incorrecta. |
