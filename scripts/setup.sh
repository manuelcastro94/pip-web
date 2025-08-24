#!/bin/bash

# CEPIP Web Setup Script

echo "🚀 Configurando CEPIP Web Application..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creando archivo .env..."
    cp backend/.env.example backend/.env
    echo "✅ Archivo .env creado. Edítalo con tus configuraciones."
fi

# Create database directory
mkdir -p database

# Build and start services
echo "🐳 Construyendo y iniciando servicios Docker..."
docker-compose up --build -d

echo "⏳ Esperando a que la base de datos esté lista..."
sleep 10

# Check if services are running
echo "🔍 Verificando servicios..."
docker-compose ps

echo ""
echo "✅ Setup completado!"
echo ""
echo "🌐 Servicios disponibles:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   PostgreSQL: localhost:5432"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Ejecutar el script de extracción: python extract_access_schema.py"
echo "   2. Revisar los logs: docker-compose logs -f"
echo "   3. Parar servicios: docker-compose down"
echo ""