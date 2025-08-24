#!/usr/bin/env python3
"""
Análisis completo de todas las relaciones entre entidades en la base de datos
"""

from sqlalchemy import create_engine, text
import re

def main():
    LOCAL_URL = "postgresql://cepip_user:cepip_password@localhost:5433/cepip_db"
    
    print("🔍 ANÁLISIS DE RELACIONES ENTRE ENTIDADES")
    print("=" * 60)
    
    try:
        local_engine = create_engine(LOCAL_URL)
        
        with local_engine.connect() as conn:
            
            # Obtener todas las tablas
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name <> 'users' 
                ORDER BY table_name
            """
            
            result = conn.execute(text(tables_query))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📊 Analizando {len(tables)} tablas:\n")
            
            relationships = {}
            foreign_keys = {}
            
            # Analizar cada tabla para encontrar relaciones
            for table in tables:
                print(f"🔎 Analizando tabla: {table}")
                
                # Obtener estructura de la tabla
                columns_query = f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position
                """
                
                columns_result = conn.execute(text(columns_query))
                columns = columns_result.fetchall()
                
                # Buscar columnas que parecen foreign keys
                fk_columns = []
                for col in columns:
                    col_name = col[0]
                    # Buscar patrones de foreign keys
                    if (col_name.endswith('id') and 
                        col_name != f'{table}id' and 
                        col_name not in ['parcelaid', 'personaid', 'enteid', 'consorcistaid'] or
                        col_name in ['enteid', 'personaid', 'consorcistaid', 'sectorid', 'rubroid', 'cargoid', 'areaid', 'camaraid', 'sindicatoid']):
                        
                        # Intentar determinar la tabla referenciada
                        if col_name == 'enteid':
                            ref_table = 'ente'
                        elif col_name == 'personaid':
                            ref_table = 'persona'
                        elif col_name == 'consorcistaid':
                            ref_table = 'consorcista'
                        elif col_name == 'sectorid':
                            ref_table = 'sector'
                        elif col_name == 'rubroid':
                            ref_table = 'rubro'
                        elif col_name == 'cargoid':
                            ref_table = 'cargo'
                        elif col_name == 'areaid':
                            ref_table = 'area'
                        elif col_name == 'camaraid':
                            ref_table = 'camara'
                        elif col_name == 'sindicatoid':
                            ref_table = 'sindicato'
                        elif col_name == 'tipoconsorcistaid':
                            ref_table = 'tipo_consorcista'
                        elif col_name == 'calleid':
                            ref_table = 'calle'
                        elif col_name == 'actividadprincipalid':
                            ref_table = 'rubro'
                        elif col_name == 'actividadsecundariaid':
                            ref_table = 'subrubro'
                        else:
                            ref_table = col_name[:-2]  # Remove 'id' suffix
                        
                        fk_columns.append((col_name, ref_table))
                
                if fk_columns:
                    foreign_keys[table] = fk_columns
                    print(f"  🔗 Relaciones encontradas:")
                    for fk_col, ref_table in fk_columns:
                        print(f"    - {table}.{fk_col} -> {ref_table}")
                else:
                    print(f"  ℹ️ No se encontraron relaciones obvias")
                
                print()
            
            # Buscar tablas de relación many-to-many
            print("🔗 TABLAS DE RELACIÓN (Many-to-Many):")
            relation_tables = [t for t in tables if 'relacion' in t or '_' in t]
            
            for table in relation_tables:
                if table in foreign_keys:
                    print(f"  📋 {table}:")
                    for fk_col, ref_table in foreign_keys[table]:
                        print(f"    - Conecta con: {ref_table} (via {fk_col})")
                
                # Mostrar algunos datos de ejemplo
                try:
                    sample_query = f"SELECT * FROM {table} LIMIT 3"
                    sample_result = conn.execute(text(sample_query))
                    samples = sample_result.fetchall()
                    if samples:
                        columns_names = list(sample_result.keys())
                        print(f"    📄 Ejemplo de datos:")
                        for sample in samples[:2]:  # Solo 2 ejemplos
                            row_data = dict(zip(columns_names, sample))
                            print(f"      {row_data}")
                    print()
                except:
                    pass
            
            # Resumen de relaciones principales
            print("\n" + "=" * 60)
            print("📋 RESUMEN DE RELACIONES PRINCIPALES:")
            print()
            
            main_entities = ['ente', 'persona', 'consorcista', 'parcela']
            
            for entity in main_entities:
                print(f"🏢 {entity.upper()}:")
                
                # Relaciones FROM esta entidad
                if entity in foreign_keys:
                    print(f"  📤 Relacionado con:")
                    for fk_col, ref_table in foreign_keys[entity]:
                        print(f"    - {ref_table} (via {fk_col})")
                
                # Relaciones TO esta entidad
                print(f"  📥 Referenciado por:")
                for table, fks in foreign_keys.items():
                    for fk_col, ref_table in fks:
                        if ref_table == entity:
                            print(f"    - {table} (via {fk_col})")
                
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()