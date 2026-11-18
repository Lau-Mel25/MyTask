FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias primero: Docker reutiliza esta capa si requirements.txt no cambia
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Archivos estáticos (CSS) que sirve WhiteNoise
RUN DJANGO_SECRET_KEY=build python manage.py collectstatic --noinput

# Carpeta de la base de datos SQLite (se monta como volumen)
RUN mkdir -p /data

# Usuario sin privilegios
RUN useradd --create-home appuser && chown -R appuser /app /data
USER appuser

EXPOSE 8000

# Aplica las migraciones, crea el administrador si hay variables DJANGO_SUPERUSER_*
# (si ya existe, el aviso se ignora) y arranca el servidor
CMD ["sh", "-c", "python manage.py migrate --noinput && { [ -z \"$DJANGO_SUPERUSER_USERNAME\" ] || python manage.py createsuperuser --noinput || true; } && gunicorn mysite.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 90"]
