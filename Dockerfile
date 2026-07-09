FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema necesarias para WeasyPrint (PDFs), Pillow y qrcode
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY gimnasio_naza/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto Django
COPY gimnasio_naza/ /app/gimnasio_naza/

WORKDIR /app/gimnasio_naza

# Carpeta donde vivirá el archivo db.sqlite3 (se monta como volumen)
RUN mkdir -p /app/gimnasio_naza/data

# collectstatic no toca la base de datos, por eso sí puede ir en el build
RUN python manage.py collectstatic --noinput

# migrate y la creación del superusuario se mueven al entrypoint (ver entrypoint.sh):
# deben correr cuando arranca el CONTENEDOR, no cuando se construye la IMAGEN, porque
# la base de datos real vive en un volumen/disco que todavía no existe durante el build.
COPY entrypoint.sh /app/gimnasio_naza/entrypoint.sh
RUN chmod +x /app/gimnasio_naza/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/gimnasio_naza/entrypoint.sh"]