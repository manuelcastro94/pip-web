FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY backend/requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY backend/ .
COPY frontend/ ./frontend/
COPY init_auth_db.py .
COPY migrate_to_production.py .

# Crear usuario no-root
RUN adduser --disabled-password --gecos '' --shell /bin/bash user && chown -R user:user /app
USER user

# Exponer puerto
EXPOSE 8000

# Comando de inicio (inicializa auth y luego inicia la app)
CMD python init_auth_db.py && uvicorn main:app --host 0.0.0.0 --port 8000