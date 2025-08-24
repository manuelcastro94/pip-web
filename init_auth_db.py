#!/usr/bin/env python3
"""
Script para inicializar las tablas de autenticación
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

def create_users_table():
    load_dotenv()
    
    # Usar DATABASE_URL de las variables de entorno
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL no está configurada")
        sys.exit(1)
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔄 Creando tabla de usuarios...")
        
        # Crear tabla users
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            google_id VARCHAR(255) UNIQUE,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            picture TEXT,
            is_active BOOLEAN DEFAULT true,
            is_admin BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        
        print("✅ Tabla 'users' creada exitosamente")
        
        # Verificar si existen usuarios
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("ℹ️  No hay usuarios registrados. El primer usuario en hacer login será administrador.")
        else:
            print(f"ℹ️  Existen {user_count} usuarios en el sistema")
        
        cursor.close()
        conn.close()
        
        print("🎉 Inicialización de autenticación completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_users_table()