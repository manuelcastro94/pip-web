#!/usr/bin/env python3
"""
Script para migrar datos desde PostgreSQL local a Railway PostgreSQL
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    # URLs de bases de datos
    LOCAL_DB_URL = "postgresql://cepip_user:cepip_password@localhost:5433/cepip_db"
    RAILWAY_DB_URL = "postgresql://postgres:KQVUDTHamyZgFEVYswoCEMQUyyyCAgxV@maglev.proxy.rlwy.net:27499/railway"
    
    print("🚀 Iniciando migración desde PostgreSQL local a Railway...")
    print(f"⏰ {datetime.now()}")
    
    # Paso 1: Exportar datos desde PostgreSQL local
    print("\n📤 Exportando datos desde PostgreSQL local...")
    dump_file = "cepip_data_export.sql"
    
    try:
        # pg_dump para exportar solo los datos (sin schema)
        dump_cmd = [
            "pg_dump",
            "--data-only",
            "--no-owner",
            "--no-privileges", 
            "--column-inserts",
            LOCAL_DB_URL,
            "-f", dump_file
        ]
        
        result = subprocess.run(dump_cmd, check=True, capture_output=True, text=True)
        print(f"✅ Datos exportados a {dump_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error exportando datos: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ pg_dump no encontrado. ¿Está PostgreSQL instalado?")
        return False
    
    # Paso 2: Importar datos a Railway PostgreSQL
    print("\n📥 Importando datos a Railway PostgreSQL...")
    
    try:
        # psql para importar los datos
        import_cmd = [
            "psql",
            RAILWAY_DB_URL,
            "-f", dump_file
        ]
        
        result = subprocess.run(import_cmd, check=True, capture_output=True, text=True)
        print("✅ Datos importados exitosamente a Railway")
        
        # Mostrar output si hay información útil
        if result.stdout.strip():
            print(f"Output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error importando datos: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ psql no encontrado. ¿Está PostgreSQL instalado?")
        return False
    
    # Paso 3: Limpiar archivo temporal
    try:
        os.remove(dump_file)
        print(f"🧹 Archivo temporal {dump_file} eliminado")
    except:
        print(f"⚠️ No se pudo eliminar {dump_file}")
    
    print(f"\n🎉 Migración completada exitosamente!")
    print(f"⏰ {datetime.now()}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)