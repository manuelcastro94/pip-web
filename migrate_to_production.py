#!/usr/bin/env python3
"""
Script para migrar datos de la base local a la base de producción
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # URL de la base de datos de producción (Railway la configurará automáticamente)
    prod_db_url = os.getenv("DATABASE_URL")
    
    if not prod_db_url:
        print("❌ ERROR: DATABASE_URL no está configurada")
        sys.exit(1)
    
    print("🚀 Iniciando migración de datos a producción...")
    
    # Ejecutar el script de migración existente pero apuntando a producción
    env = os.environ.copy()
    env["DATABASE_URL"] = prod_db_url
    
    try:
        # Ejecutar migración
        result = subprocess.run([
            sys.executable, "migrate_data_mdb.py"
        ], env=env, check=True, capture_output=True, text=True)
        
        print("✅ Migración completada exitosamente!")
        print(f"Registros migrados: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error durante la migración: {e}")
        print(f"Salida de error: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ No se encontró el script migrate_data_mdb.py")
        print("Este script debe ejecutarse desde la raíz del proyecto")
        sys.exit(1)

if __name__ == "__main__":
    main()