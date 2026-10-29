# Imagen de la API de Las Palomas Festival (FastAPI) para Render
FROM python:3.12-slim

# Salida de logs sin buffer y sin .pyc en disco
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primero, para aprovechar la caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la API y datos de ejemplo
COPY app ./app
COPY seed.py ./seed.py

# Carpeta de subidas (biblioteca de medios)
RUN mkdir -p uploads

# Usuario sin privilegios
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Render inyecta $PORT; en local cae a 8000
ENV PORT=8000
EXPOSE 8000

# Shell form para que $PORT se expanda en tiempo de ejecución
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
