#!/usr/bin/env python3
"""
Verificación completa de migración - comparar TODAS las tablas
"""

from sqlalchemy import create_engine, text

def main():
    LOCAL_URL = "postgresql://cepip_user:cepip_password@localhost:5433/cepip_db"
    RAILWAY_URL = "postgresql://postgres:KQVUDTHamyZgFEVYswoCEMQUyyyCAgxV@maglev.proxy.rlwy.net:27499/railway"
    
    print("🔍 VERIFICACIÓN COMPLETA DE MIGRACIÓN")
    print("=" * 50)
    
    try:
        local_engine = create_engine(LOCAL_URL)
        railway_engine = create_engine(RAILWAY_URL)
        
        with local_engine.connect() as local_conn, railway_engine.connect() as railway_conn:
            
            # Obtener lista de todas las tablas (excluyendo 'users')
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name <> 'users' 
                ORDER BY table_name
            """
            
            result = local_conn.execute(text(tables_query))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📊 Verificando {len(tables)} tablas:\n")
            
            total_local = 0
            total_railway = 0
            missing_tables = []
            incomplete_tables = []
            complete_tables = []
            
            for table in tables:
                try:
                    # Contar en local
                    local_count = local_conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    total_local += local_count
                    
                    # Contar en Railway
                    try:
                        railway_count = railway_conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                        total_railway += railway_count
                    except:
                        railway_count = "ERROR/NO EXISTE"
                    
                    # Comparar
                    if railway_count == "ERROR/NO EXISTE":
                        missing_tables.append(table)
                        status = "❌ FALTA"
                    elif local_count == railway_count:
                        complete_tables.append(table)
                        status = "✅ OK"
                    else:
                        incomplete_tables.append((table, local_count, railway_count))
                        status = f"⚠️ PARCIAL ({railway_count}/{local_count})"
                    
                    print(f"{table:<25} | Local: {local_count:<6} | Railway: {railway_count:<6} | {status}")
                    
                except Exception as e:
                    print(f"{table:<25} | ERROR: {e}")
            
            print("\n" + "=" * 70)
            print("📋 RESUMEN:")
            print(f"  📊 Total registros LOCAL:   {total_local:,}")
            print(f"  📊 Total registros RAILWAY: {total_railway:,}")
            print(f"  ✅ Tablas completas:        {len(complete_tables)}")
            print(f"  ⚠️ Tablas incompletas:      {len(incomplete_tables)}")
            print(f"  ❌ Tablas faltantes:        {len(missing_tables)}")
            
            if missing_tables:
                print(f"\n❌ TABLAS FALTANTES:")
                for table in missing_tables:
                    print(f"  - {table}")
            
            if incomplete_tables:
                print(f"\n⚠️ TABLAS INCOMPLETAS:")
                for table, local_count, railway_count in incomplete_tables:
                    print(f"  - {table}: {railway_count}/{local_count} registros")
            
            if len(complete_tables) == len(tables):
                print(f"\n🎉 ¡MIGRACIÓN 100% COMPLETA!")
            else:
                print(f"\n⚠️ MIGRACIÓN INCOMPLETA - Faltan {len(tables) - len(complete_tables)} tablas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()