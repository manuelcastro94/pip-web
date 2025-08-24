"""
Tables API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any

from ..database import get_db

router = APIRouter()

@router.get("/")
async def get_tables(db: Session = Depends(get_db)):
    """
    Get list of available tables and their schemas
    """
    try:
        # Get real table information from CEPIP database
        cepip_tables = [
            {
                "name": "ente",
                "label": "Entes (Empresas)",
                "description": "Empresas y entidades del parque industrial",
                "columns": [
                    {"name": "enteid", "label": "ID", "type": "number", "primary_key": True},
                    {"name": "razonsocial", "label": "Razón Social", "type": "text"},
                    {"name": "cuit", "label": "CUIT", "type": "number"},
                    {"name": "nro_socio_cepip", "label": "N° Socio CEPIP", "type": "number"},
                    {"name": "web", "label": "Sitio Web", "type": "text"},
                    {"name": "es_socio", "label": "Es Socio", "type": "boolean"},
                    {"name": "esconsorcista", "label": "Es Consorcista", "type": "boolean"}
                ],
                "record_count": db.execute(text("SELECT COUNT(*) FROM ente")).scalar()
            },
            {
                "name": "persona", 
                "label": "Personas",
                "description": "Personas asociadas a las empresas",
                "columns": [
                    {"name": "personaid", "label": "ID", "type": "number", "primary_key": True},
                    {"name": "nombre_apellido", "label": "Nombre y Apellido", "type": "text"},
                    {"name": "telefono", "label": "Teléfono", "type": "text"},
                    {"name": "celular", "label": "Celular", "type": "text"},
                    {"name": "correo_electronico", "label": "Email", "type": "email"}
                ],
                "record_count": db.execute(text("SELECT COUNT(*) FROM persona")).scalar()
            },
            {
                "name": "consorcista",
                "label": "Consorcistas", 
                "description": "Consorcistas del parque industrial",
                "columns": [
                    {"name": "consorcistaid", "label": "ID", "type": "number", "primary_key": True},
                    {"name": "nombre", "label": "Nombre", "type": "text"},
                    {"name": "nro_consorcista", "label": "N° Consorcista", "type": "number"},
                    {"name": "fecha_de_carga", "label": "Fecha de Carga", "type": "date"}
                ],
                "record_count": db.execute(text("SELECT COUNT(*) FROM consorcista")).scalar()
            },
            {
                "name": "parcela",
                "label": "Parcelas",
                "description": "Parcelas del parque industrial", 
                "columns": [
                    {"name": "parcelaid", "label": "ID", "type": "number", "primary_key": True},
                    {"name": "parcela", "label": "Parcela", "type": "text"},
                    {"name": "calle", "label": "Calle", "type": "text"},
                    {"name": "numero", "label": "Número", "type": "number"},
                    {"name": "superficie_has", "label": "Superficie (ha)", "type": "number"},
                    {"name": "tieneplanta", "label": "Tiene Planta", "type": "boolean"},
                    {"name": "alquilada", "label": "Alquilada", "type": "boolean"}
                ],
                "record_count": db.execute(text("SELECT COUNT(*) FROM parcela")).scalar()
            },
            {
                "name": "sector",
                "label": "Sectores",
                "description": "Sectores económicos",
                "columns": [
                    {"name": "sectorid", "label": "ID", "type": "number", "primary_key": True},
                    {"name": "sector", "label": "Sector", "type": "text"}
                ],
                "record_count": db.execute(text("SELECT COUNT(*) FROM sector")).scalar()
            }
        ]
        
        return {"tables": cepip_tables}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{table_name}/schema")
async def get_table_schema(table_name: str, db: Session = Depends(get_db)):
    """
    Get detailed schema for a specific table
    """
    try:
        # Mock schema for the requested table
        # This would come from database metadata in real implementation
        
        schemas = {
            "clientes": {
                "name": "clientes",
                "label": "Clientes",
                "columns": [
                    {"name": "id", "label": "ID", "type": "number", "primary_key": True, "auto_increment": True},
                    {"name": "nombre", "label": "Nombre", "type": "text", "required": True, "max_length": 100},
                    {"name": "email", "label": "Email", "type": "email", "max_length": 150},
                    {"name": "telefono", "label": "Teléfono", "type": "text", "max_length": 20},
                    {"name": "direccion", "label": "Dirección", "type": "longtext"},
                    {"name": "fecha_registro", "label": "Fecha Registro", "type": "date", "default": "CURRENT_DATE"},
                    {"name": "activo", "label": "Activo", "type": "boolean", "default": True}
                ],
                "indexes": ["email"],
                "relationships": [
                    {"table": "ordenes", "foreign_key": "cliente_id", "type": "one_to_many"}
                ]
            }
        }
        
        if table_name not in schemas:
            raise HTTPException(status_code=404, detail="Table not found")
        
        return schemas[table_name]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))