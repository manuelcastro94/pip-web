#!/usr/bin/env python3
"""
Data migration script from Access to PostgreSQL
Requires: pip install pypyodbc psycopg2-binary pandas sqlalchemy
"""

import pypyodbc
import psycopg2
import pandas as pd
import json
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("cepip-web/backend/.env")

class DataMigrator:
    def __init__(self, access_db_path, postgres_url):
        self.access_db_path = access_db_path
        self.postgres_url = postgres_url
        self.schema_info = {}
        
    def connect_access(self):
        """Connect to Access database"""
        conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.access_db_path};'
        try:
            return pypyodbc.connect(conn_str)
        except Exception as e:
            print(f"Error connecting to Access: {e}")
            return None
    
    def connect_postgres(self):
        """Connect to PostgreSQL database"""
        try:
            return create_engine(self.postgres_url)
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return None
    
    def load_schema_info(self):
        """Load schema info from JSON file"""
        if os.path.exists("access_schema.json"):
            with open("access_schema.json", "r", encoding="utf-8") as f:
                self.schema_info = json.load(f)
            print(f"✅ Schema loaded: {len(self.schema_info)} tables found")
        else:
            print("❌ Schema file not found. Run extract_access_schema.py first.")
            return False
        return True
    
    def create_postgres_tables(self, pg_engine):
        """Create PostgreSQL tables based on schema"""
        print("🗄️ Creating PostgreSQL tables...")
        
        type_mapping = {
            'LONGCHAR': 'TEXT',
            'VARCHAR': 'VARCHAR(255)',
            'INTEGER': 'INTEGER',
            'DOUBLE': 'DOUBLE PRECISION',
            'DATETIME': 'TIMESTAMP',
            'BIT': 'BOOLEAN',
            'LONGBINARY': 'BYTEA',
            'CURRENCY': 'DECIMAL(10,2)',
            'SINGLE': 'REAL',
            'BYTE': 'SMALLINT'
        }
        
        for table_name, table_info in self.schema_info.items():
            print(f"  Creating table: {table_name}")
            
            # Build CREATE TABLE statement
            columns = []
            for col in table_info['columns']:
                pg_type = type_mapping.get(col['type'], 'TEXT')
                nullable = "" if col['nullable'] else " NOT NULL"
                
                # Add PRIMARY KEY if this is an ID field
                if col['name'].lower() in ['id', 'id_' + table_name.lower()]:
                    columns.append(f"{col['name']} SERIAL PRIMARY KEY")
                else:
                    columns.append(f"{col['name']} {pg_type}{nullable}")
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(columns) + "\n);"
            
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text(create_sql))
                    conn.commit()
                print(f"  ✅ Table {table_name} created")
            except Exception as e:
                print(f"  ❌ Error creating table {table_name}: {e}")
    
    def migrate_table_data(self, table_name, access_conn, pg_engine):
        """Migrate data from Access table to PostgreSQL"""
        print(f"📊 Migrating data for table: {table_name}")
        
        try:
            # Read data from Access
            query = f"SELECT * FROM [{table_name}]"
            df = pd.read_sql(query, access_conn)
            
            if df.empty:
                print(f"  ⚠️ No data found in {table_name}")
                return
            
            # Clean column names (remove spaces, special characters)
            df.columns = [col.replace(' ', '_').replace('-', '_') for col in df.columns]
            
            # Convert data types
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Handle potential datetime strings
                    try:
                        df[col] = pd.to_datetime(df[col], errors='ignore')
                    except:
                        pass
            
            # Insert into PostgreSQL
            df.to_sql(table_name, pg_engine, if_exists='append', index=False, method='multi')
            
            print(f"  ✅ Migrated {len(df)} records to {table_name}")
            
        except Exception as e:
            print(f"  ❌ Error migrating {table_name}: {e}")
    
    def run_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting CEPIP data migration...")
        print("=" * 50)
        
        # Load schema information
        if not self.load_schema_info():
            return False
        
        # Connect to databases
        print("🔌 Connecting to databases...")
        access_conn = self.connect_access()
        if not access_conn:
            print("❌ Could not connect to Access database")
            return False
        
        pg_engine = self.connect_postgres()
        if not pg_engine:
            print("❌ Could not connect to PostgreSQL database")
            return False
        
        print("✅ Database connections established")
        
        # Create PostgreSQL tables
        self.create_postgres_tables(pg_engine)
        
        # Migrate data for each table
        print("\n📦 Starting data migration...")
        migrated_tables = 0
        total_records = 0
        
        for table_name in self.schema_info.keys():
            try:
                self.migrate_table_data(table_name, access_conn, pg_engine)
                migrated_tables += 1
                total_records += self.schema_info[table_name].get('row_count', 0)
            except Exception as e:
                print(f"❌ Failed to migrate table {table_name}: {e}")
        
        # Close connections
        access_conn.close()
        pg_engine.dispose()
        
        # Migration summary
        print("\n" + "=" * 50)
        print("📋 Migration Summary:")
        print(f"  Tables migrated: {migrated_tables}/{len(self.schema_info)}")
        print(f"  Total records: ~{total_records}")
        print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ Migration completed successfully!")
        
        return True

def main():
    # Configuration
    access_db_path = "Copia Base de Datos - CEPIP - def_be.accdb"
    postgres_url = os.getenv("DATABASE_URL", "postgresql://cepip_user:cepip_password@localhost:5432/cepip_db")
    
    # Check if Access database exists
    if not os.path.exists(access_db_path):
        print(f"❌ Access database not found: {access_db_path}")
        print("Please make sure the Access database file is in the current directory")
        sys.exit(1)
    
    # Run migration
    migrator = DataMigrator(access_db_path, postgres_url)
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration completed! Next steps:")
        print("1. Start the web application: cd cepip-web && ./scripts/dev.sh start")
        print("2. Open the application: http://localhost")
        print("3. Check the API docs: http://localhost:8000/docs")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()