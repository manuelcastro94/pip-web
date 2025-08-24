#!/bin/bash

# Development helper script for CEPIP

case "$1" in
    "start")
        echo "🚀 Iniciando servicios de desarrollo..."
        docker-compose up -d
        echo "✅ Servicios iniciados"
        echo "   Frontend: http://localhost"
        echo "   Backend: http://localhost:8000"
        ;;
    
    "stop")
        echo "🛑 Deteniendo servicios..."
        docker-compose down
        echo "✅ Servicios detenidos"
        ;;
    
    "restart")
        echo "🔄 Reiniciando servicios..."
        docker-compose restart
        echo "✅ Servicios reiniciados"
        ;;
    
    "logs")
        service=${2:-""}
        if [ -z "$service" ]; then
            docker-compose logs -f
        else
            docker-compose logs -f "$service"
        fi
        ;;
    
    "extract")
        echo "📊 Extrayendo esquema de Access..."
        cd .. && python extract_access_schema.py
        ;;
    
    "migrate")
        echo "🗄️ Ejecutando migraciones..."
        docker-compose exec backend python -c "
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
print('Migraciones ejecutadas')
"
        ;;
    
    "shell")
        service=${2:-"backend"}
        echo "🐚 Abriendo shell en $service..."
        docker-compose exec "$service" /bin/bash
        ;;
    
    "psql")
        echo "🐘 Conectando a PostgreSQL..."
        docker-compose exec db psql -U cepip_user -d cepip_db
        ;;
    
    "clean")
        echo "🧹 Limpiando containers y volúmenes..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Limpieza completada"
        ;;
    
    *)
        echo "CEPIP Development Helper"
        echo ""
        echo "Uso: ./dev.sh [comando]"
        echo ""
        echo "Comandos disponibles:"
        echo "  start     - Iniciar servicios"
        echo "  stop      - Detener servicios"  
        echo "  restart   - Reiniciar servicios"
        echo "  logs      - Ver logs (opcional: especificar servicio)"
        echo "  extract   - Extraer esquema de Access"
        echo "  migrate   - Ejecutar migraciones de DB"
        echo "  shell     - Abrir shell (opcional: especificar servicio)"
        echo "  psql      - Conectar a PostgreSQL"
        echo "  clean     - Limpiar containers y volúmenes"
        echo ""
        echo "Ejemplos:"
        echo "  ./dev.sh start"
        echo "  ./dev.sh logs backend"
        echo "  ./dev.sh shell frontend"
        ;;
esac