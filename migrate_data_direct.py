#!/usr/bin/env python3
"""
Migración directa de datos usando Python y SQLAlchemy
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData
from datetime import datetime

def migrate_data():
    # URLs de conexión
    LOCAL_URL = "postgresql://cepip_user:cepip_password@localhost:5433/cepip_db"
    RAILWAY_URL = "postgresql://postgres:KQVUDTHamyZgFEVYswoCEMQUyyyCAgxV@maglev.proxy.rlwy.net:27499/railway"
    
    print("🚀 Iniciando migración directa de datos...")
    print(f"⏰ {datetime.now()}")
    
    try:
        # Conectar a ambas bases
        print("\n🔌 Conectando a bases de datos...")
        local_engine = create_engine(LOCAL_URL)
        railway_engine = create_engine(RAILWAY_URL)
        
        local_conn = local_engine.connect()
        railway_conn = railway_engine.connect()
        
        print("✅ Conexiones establecidas")
        
        # Obtener lista de tablas (excluyendo tablas de sistema)
        tables_query = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name != 'users'
        ORDER BY table_name
        """
        
        result = local_conn.execute(text(tables_query))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"\n📊 Tablas a migrar: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        total_records = 0
        
        # Migrar cada tabla
        for table_name in tables:
            print(f"\n📋 Migrando tabla: {table_name}")
            
            # Leer datos de la tabla local
            select_query = f"SELECT * FROM {table_name}"
            local_data = local_conn.execute(text(select_query)).fetchall()
            
            if not local_data:
                print(f"  ⚠️ Tabla {table_name} está vacía")
                continue
            
            # Obtener nombres de columnas
            columns_result = local_conn.execute(text(f"SELECT * FROM {table_name} LIMIT 0"))
            column_names = list(columns_result.keys())
            
            print(f"  📝 {len(local_data)} registros encontrados")
            
            # Limpiar tabla de destino (si existe)
            try:
                railway_conn.execute(text(f"DELETE FROM {table_name}"))
                railway_conn.commit()
            except:
                pass  # La tabla podría no existir aún
            
            # Insertar datos
            success_count = 0
            for row in local_data:
                try:
                    # Crear query de inserción con placeholders
                    placeholders = ', '.join([f':{col}' for col in column_names])
                    insert_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                    
                    # Crear diccionario de valores
                    row_dict = dict(zip(column_names, row))
                    
                    railway_conn.execute(text(insert_query), row_dict)
                    success_count += 1
                    
                except Exception as e:
                    print(f"    ❌ Error insertando registro: {e}")
                    continue
            
            # Commit los cambios
            railway_conn.commit()
            total_records += success_count
            print(f"  ✅ {success_count}/{len(local_data)} registros migrados")
        
        print(f"\n🎉 Migración completada!")
        print(f"📊 Total de registros migrados: {total_records}")
        print(f"⏰ {datetime.now()}")
        
        # Cerrar conexiones
        local_conn.close()
        railway_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)