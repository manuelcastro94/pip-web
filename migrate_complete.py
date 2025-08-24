#!/usr/bin/env python3
"""
Migración completa: schema + datos desde PostgreSQL local a Railway
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

def main():
    LOCAL_URL = "postgresql://cepip_user:cepip_password@localhost:5433/cepip_db"
    RAILWAY_URL = "postgresql://postgres:KQVUDTHamyZgFEVYswoCEMQUyyyCAgxV@maglev.proxy.rlwy.net:27499/railway"
    
    print("🚀 Migración completa: Schema + Datos")
    print(f"⏰ {datetime.now()}")
    
    try:
        # Conectar a ambas bases
        print("\n🔌 Conectando a bases de datos...")
        local_engine = create_engine(LOCAL_URL)
        railway_engine = create_engine(RAILWAY_URL)
        
        with local_engine.connect() as local_conn, railway_engine.connect() as railway_conn:
            print("✅ Conexiones establecidas")
            
            # PASO 1: Exportar y crear schema
            print("\n📋 Creando schema en Railway...")
            
            # Exportar solo las definiciones de tabla (sin la tabla users)
            schema_query = """
                SELECT 
                    'CREATE TABLE ' || table_name || ' (' ||
                    string_agg(
                        column_name || ' ' || 
                        CASE 
                            WHEN data_type = 'character varying' THEN 'VARCHAR(' || character_maximum_length || ')'
                            WHEN data_type = 'numeric' THEN 'NUMERIC(' || numeric_precision || ',' || numeric_scale || ')'
                            WHEN data_type = 'integer' THEN 'INTEGER'
                            WHEN data_type = 'bigint' THEN 'BIGINT'
                            WHEN data_type = 'double precision' THEN 'DOUBLE PRECISION'
                            WHEN data_type = 'timestamp without time zone' THEN 'TIMESTAMP'
                            WHEN data_type = 'date' THEN 'DATE'
                            WHEN data_type = 'boolean' THEN 'BOOLEAN'
                            WHEN data_type = 'text' THEN 'TEXT'
                            ELSE data_type
                        END ||
                        CASE 
                            WHEN is_nullable = 'NO' THEN ' NOT NULL'
                            ELSE ''
                        END,
                        ', '
                        ORDER BY ordinal_position
                    ) || ');' as create_statement
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name != 'users'
                GROUP BY table_name
                ORDER BY table_name;
            """
            
            result = local_conn.execute(text(schema_query))
            create_statements = [row[0] for row in result.fetchall()]
            
            # Crear tablas en Railway
            for create_stmt in create_statements:
                try:
                    railway_conn.execute(text(create_stmt))
                    print(f"  ✅ Tabla creada")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"  ⚠️ Tabla ya existe, continuando...")
                    else:
                        print(f"  ❌ Error creando tabla: {e}")
                        continue
            
            railway_conn.commit()
            print(f"✅ Schema creado ({len(create_statements)} tablas)")
            
            # PASO 2: Migrar datos
            print("\n📊 Migrando datos...")
            
            # Obtener lista de tablas
            tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name != 'users'
                ORDER BY table_name
            """
            
            result = local_conn.execute(text(tables_query))
            tables = [row[0] for row in result.fetchall()]
            
            total_records = 0
            
            for table_name in tables:
                print(f"\n📋 {table_name}")
                
                # Contar registros
                count_result = local_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                record_count = count_result.scalar()
                
                if record_count == 0:
                    print(f"  ⚠️ Vacía")
                    continue
                
                print(f"  📝 {record_count} registros")
                
                # Limpiar tabla destino
                railway_conn.execute(text(f"DELETE FROM {table_name}"))
                
                # Copiar datos por lotes
                batch_size = 100
                offset = 0
                success_count = 0
                
                while offset < record_count:
                    # Leer lote
                    batch_query = f"SELECT * FROM {table_name} ORDER BY 1 LIMIT {batch_size} OFFSET {offset}"
                    batch_data = local_conn.execute(text(batch_query)).fetchall()
                    
                    if not batch_data:
                        break
                    
                    # Obtener nombres de columnas
                    columns_result = local_conn.execute(text(f"SELECT * FROM {table_name} LIMIT 0"))
                    column_names = list(columns_result.keys())
                    
                    # Insertar lote
                    for row in batch_data:
                        try:
                            placeholders = ', '.join([f':{col}' for col in column_names])
                            insert_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
                            row_dict = dict(zip(column_names, row))
                            railway_conn.execute(text(insert_query), row_dict)
                            success_count += 1
                        except Exception as e:
                            print(f"    ❌ Error: {e}")
                            continue
                    
                    offset += batch_size
                    print(f"  📈 {success_count}/{record_count}")
                
                railway_conn.commit()
                total_records += success_count
                print(f"  ✅ {success_count} registros migrados")
            
            print(f"\n🎉 Migración completada!")
            print(f"📊 Total: {total_records} registros")
            print(f"⏰ {datetime.now()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)