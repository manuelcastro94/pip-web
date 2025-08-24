#!/usr/bin/env python3
"""
Completar migración de las tablas faltantes
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

def main():
    LOCAL_URL = "postgresql://cepip_user:cepip_password@localhost:5433/cepip_db"
    RAILWAY_URL = "postgresql://postgres:KQVUDTHamyZgFEVYswoCEMQUyyyCAgxV@maglev.proxy.rlwy.net:27499/railway"
    
    # Tablas que faltan migrar
    missing_tables = ['persona', 'parcela', 'relacion_ente_persona']
    
    print("🚀 Completando migración de tablas faltantes")
    print(f"📋 Tablas: {', '.join(missing_tables)}")
    print(f"⏰ {datetime.now()}")
    
    try:
        # Conectar a ambas bases
        print("\n🔌 Conectando a bases de datos...")
        local_engine = create_engine(LOCAL_URL)
        railway_engine = create_engine(RAILWAY_URL)
        
        with local_engine.connect() as local_conn, railway_engine.connect() as railway_conn:
            print("✅ Conexiones establecidas")
            
            total_migrated = 0
            
            for table_name in missing_tables:
                print(f"\n📋 Migrando tabla: {table_name}")
                
                # Contar registros en origen
                count_result = local_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                record_count = count_result.scalar()
                
                if record_count == 0:
                    print(f"  ⚠️ Tabla {table_name} está vacía en origen")
                    continue
                
                print(f"  📝 {record_count} registros en origen")
                
                # Limpiar tabla destino
                try:
                    railway_conn.execute(text(f"DELETE FROM {table_name}"))
                    railway_conn.commit()
                    print(f"  🧹 Tabla {table_name} limpiada en destino")
                except Exception as e:
                    print(f"  ⚠️ Error limpiando tabla: {e}")
                
                # Obtener estructura de la tabla
                columns_result = local_conn.execute(text(f"SELECT * FROM {table_name} LIMIT 0"))
                column_names = list(columns_result.keys())
                print(f"  📊 Columnas: {', '.join(column_names)}")
                
                # Migrar por lotes
                batch_size = 50  # Lotes más pequeños para evitar timeouts
                offset = 0
                success_count = 0
                error_count = 0
                
                while offset < record_count:
                    print(f"  📈 Procesando registros {offset+1}-{min(offset+batch_size, record_count)}")
                    
                    # Leer lote
                    batch_query = f"""
                        SELECT * FROM {table_name} 
                        ORDER BY 1 
                        LIMIT {batch_size} OFFSET {offset}
                    """
                    batch_data = local_conn.execute(text(batch_query)).fetchall()
                    
                    if not batch_data:
                        break
                    
                    # Insertar cada registro del lote
                    for row in batch_data:
                        try:
                            # Crear query de inserción
                            placeholders = ', '.join([f':{col}' for col in column_names])
                            insert_query = f"""
                                INSERT INTO {table_name} ({', '.join(column_names)}) 
                                VALUES ({placeholders})
                            """
                            
                            # Crear diccionario de valores
                            row_dict = dict(zip(column_names, row))
                            
                            # Ejecutar inserción
                            railway_conn.execute(text(insert_query), row_dict)
                            success_count += 1
                            
                        except Exception as e:
                            error_count += 1
                            print(f"    ❌ Error insertando registro: {e}")
                            # Rollback y continuar
                            railway_conn.rollback()
                            continue
                    
                    # Commit el lote
                    try:
                        railway_conn.commit()
                    except Exception as e:
                        print(f"    ❌ Error en commit: {e}")
                        railway_conn.rollback()
                    
                    offset += batch_size
                
                total_migrated += success_count
                print(f"  ✅ {success_count}/{record_count} registros migrados ({error_count} errores)")
                
                # Verificar resultado
                verify_result = railway_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                final_count = verify_result.scalar()
                print(f"  🔍 Verificación: {final_count} registros en Railway")
            
            print(f"\n🎉 Migración completada!")
            print(f"📊 Total registros migrados: {total_migrated}")
            print(f"⏰ {datetime.now()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)