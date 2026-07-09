#!/bin/sh
set -e

echo "==> Aplicando migraciones..."
python manage.py migrate --noinput

echo "==> Recolectando estáticos (por si acaso)..."
python manage.py collectstatic --noinput

# ------------------------------------------------------------------
# Crea el superusuario "Samir" automáticamente si no existe todavía.
# Un superusuario (is_superuser=True) entra directo al Dashboard sin
# necesitar un perfil "Usuario" adicional (gimnasio/views/Dashboard
# ya lo deja pasar con user.is_superuser).
#
# Los valores por defecto de abajo se usan SOLO si no defines estas
# variables en el Dashboard de Render (Environment). Se recomienda
# definirlas ahí para no dejar la contraseña real en el código/git.
# ------------------------------------------------------------------
DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:zamir}"
DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:zamirdavida242@gmail.com}"
DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-zamyr2580}"
export DJANGO_SUPERUSER_USERNAME DJANGO_SUPERUSER_EMAIL DJANGO_SUPERUSER_PASSWORD

echo "==> Verificando/creando superusuario ${DJANGO_SUPERUSER_USERNAME}..."
python manage.py shell -c "
from django.contrib.auth.models import User
import os

username = os.environ['DJANGO_SUPERUSER_USERNAME']
email = os.environ['DJANGO_SUPERUSER_EMAIL']
password = os.environ['DJANGO_SUPERUSER_PASSWORD']

if User.objects.filter(username=username).exists():
    print(f\"==> El superusuario '{username}' ya existe, no se crea de nuevo.\")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f\"==> Superusuario '{username}' creado correctamente.\")
"

echo "==> Iniciando gunicorn en el puerto ${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 1 \
    --threads 2 \
    --timeout 120
