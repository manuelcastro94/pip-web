"""
Records API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import json
import os

from ..database import get_db
from ..auth import get_current_user

router = APIRouter()

@router.get("/{table_name}")
async def get_records(
    table_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated records from a table
    """
    try:
        # Validate table name to prevent SQL injection
        valid_tables = ['ente', 'persona', 'consorcista', 'parcela', 'sector', 'rubro', 'subrubro', 'area', 'cargo', 'camara', 'sindicato']
        if table_name not in valid_tables:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total = count_result.scalar()
        
        # Get paginated data with JOINs for better display
        if table_name == 'parcela':
            # Join with consorcista to get the name
            query = """
                SELECT p.*, c.nombre as consorcista_nombre 
                FROM parcela p 
                LEFT JOIN consorcista c ON p.consorcistaid = c.consorcistaid 
                ORDER BY p.parcelaid 
                LIMIT :limit OFFSET :offset
            """
        elif table_name == 'ente':
            # Join with sector and rubro for empresas (through subrubro)
            query = """
                SELECT e.*, s.sector as sector_nombre, r.rubro as rubro_nombre, sr.subrubro as subrubro_nombre
                FROM ente e 
                LEFT JOIN subrubro sr ON e.actividadprincipalid = sr.subrubroid 
                LEFT JOIN rubro r ON sr.rubroid = r.rubroid 
                LEFT JOIN sector s ON r.sectorid = s.sectorid 
                ORDER BY e.enteid 
                LIMIT :limit OFFSET :offset
            """
        elif table_name == 'persona':
            # Join with relaciones to get empresas and cargos
            query = """
                SELECT p.*, 
                       STRING_AGG(DISTINCT e.razonsocial, ', ' ORDER BY e.razonsocial) as empresas,
                       STRING_AGG(DISTINCT c.cargo, ', ' ORDER BY c.cargo) as cargos
                FROM persona p 
                LEFT JOIN relacion_ente_persona rep ON p.personaid = rep.personaid 
                LEFT JOIN ente e ON rep.enteid = e.enteid 
                LEFT JOIN cargo c ON rep.cargoid = c.cargoid 
                GROUP BY p.personaid, p.fecha_de_carga, p.nombre_apellido, p.telefono, p.celular, p.correo_electronico, p.consorcistaid
                ORDER BY p.personaid 
                LIMIT :limit OFFSET :offset
            """
        elif table_name == 'consorcista':
            # Join with tipo and count parcelas/empresas
            query = """
                SELECT c.*, 
                       tc.tipo as tipo_nombre,
                       COUNT(DISTINCT p.parcelaid) as parcelas_count,
                       COUNT(DISTINCT e.enteid) as empresas_count
                FROM consorcista c 
                LEFT JOIN tipo_consorcista tc ON c.tipoid = tc.tipoconsorcistaid 
                LEFT JOIN parcela p ON c.consorcistaid = p.consorcistaid 
                LEFT JOIN ente e ON c.consorcistaid = e.consorcistaid 
                GROUP BY c.consorcistaid, c.nombre, c.nro_consorcista, c.tipoid, c.fecha_de_carga, tc.tipo
                ORDER BY c.consorcistaid 
                LIMIT :limit OFFSET :offset
            """
        else:
            query = f"SELECT * FROM {table_name} ORDER BY 1 LIMIT :limit OFFSET :offset"
        
        result = db.execute(text(query), {"limit": limit, "offset": offset})
        
        # Convert to list of dictionaries
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        # Define column metadata for each table
        table_columns = {
            'ente': [
                {"name": "enteid", "label": "ID", "type": "number"},
                {"name": "razonsocial", "label": "Razón Social", "type": "text"},
                {"name": "cuit", "label": "CUIT", "type": "number"},
                {"name": "nro_socio_cepip", "label": "N° Socio CEPIP", "type": "number"},
                {"name": "sector_nombre", "label": "Sector", "type": "text"},
                {"name": "rubro_nombre", "label": "Rubro", "type": "text"},
                {"name": "es_socio", "label": "Es Socio", "type": "boolean"},
                {"name": "esconsorcista", "label": "Es Consorcista", "type": "boolean"},
                {"name": "web", "label": "Web", "type": "text"}
            ],
            'persona': [
                {"name": "personaid", "label": "ID", "type": "number"},
                {"name": "nombre_apellido", "label": "Nombre y Apellido", "type": "text"},
                {"name": "correo_electronico", "label": "Email", "type": "email"},
                {"name": "telefono", "label": "Teléfono", "type": "text"},
                {"name": "celular", "label": "Celular", "type": "text"},
                {"name": "empresas", "label": "Empresas", "type": "text"},
                {"name": "cargos", "label": "Cargos", "type": "text"}
            ],
            'consorcista': [
                {"name": "consorcistaid", "label": "ID", "type": "number"},
                {"name": "nombre", "label": "Nombre", "type": "text"},
                {"name": "nro_consorcista", "label": "N° Consorcista", "type": "number"},
                {"name": "tipo_nombre", "label": "Tipo", "type": "text"},
                {"name": "parcelas_count", "label": "Parcelas", "type": "number"},
                {"name": "empresas_count", "label": "Empresas", "type": "number"},
                {"name": "fecha_de_carga", "label": "Fecha Carga", "type": "date"}
            ],
            'parcela': [
                {"name": "parcelaid", "label": "ID", "type": "number"},
                {"name": "parcela", "label": "Parcela", "type": "text"},
                {"name": "calle", "label": "Calle", "type": "text"},
                {"name": "numero", "label": "Número", "type": "number"},
                {"name": "superficie_has", "label": "Superficie (ha)", "type": "number"},
                {"name": "tieneplanta", "label": "Tiene Planta", "type": "boolean"},
                {"name": "alquilada", "label": "Alquilada", "type": "boolean"},
                {"name": "consorcista_nombre", "label": "Consorcista", "type": "text"}
            ]
        }
        
        return {
            "data": data,
            "columns": table_columns.get(table_name, []),
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/empresas")
async def get_empresas_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get list of empresas for dropdowns
    """
    try:
        query = "SELECT enteid, razonsocial FROM ente ORDER BY razonsocial"
        result = db.execute(text(query))
        empresas = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"empresas": empresas}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/cargos")
async def get_cargos_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get list of cargos for dropdowns
    """
    try:
        query = "SELECT cargoid, cargo FROM cargo ORDER BY cargo"
        result = db.execute(text(query))
        cargos = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"cargos": cargos}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/areas")
async def get_areas_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get list of areas for dropdowns
    """
    try:
        query = "SELECT areaid, area FROM area ORDER BY area"
        result = db.execute(text(query))
        areas = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"areas": areas}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/consorcistas")
async def get_consorcistas_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get list of consorcistas for dropdowns
    """
    try:
        query = "SELECT consorcistaid, nombre FROM consorcista ORDER BY nombre"
        result = db.execute(text(query))
        consorcistas = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"consorcistas": consorcistas}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/tipos-consorcista")
async def get_tipos_consorcista_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get list of tipos de consorcista for dropdowns
    """
    try:
        query = "SELECT tipoconsorcistaid, tipo FROM tipo_consorcista ORDER BY tipo"
        result = db.execute(text(query))
        tipos = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"tipos": tipos}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/persona/{persona_id}/relaciones")
async def create_persona_relation(
    persona_id: int,
    relation_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a relation between persona and empresa with cargo
    """
    try:
        query = """
            INSERT INTO relacion_ente_persona (enteid, personaid, cargoid, areaid, fecha_de_carga)
            VALUES (:enteid, :personaid, :cargoid, :areaid, CURRENT_DATE)
        """
        
        result = db.execute(text(query), {
            "enteid": relation_data.get("enteid"),
            "personaid": persona_id,
            "cargoid": relation_data.get("cargoid"),
            "areaid": relation_data.get("areaid")
        })
        db.commit()
        
        return {"message": "Relación creada exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/persona/{persona_id}/relaciones")
async def get_persona_relations(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all relations for a persona
    """
    try:
        query = """
            SELECT rep.ente_persona_id, rep.enteid, rep.cargoid, rep.areaid,
                   e.razonsocial, c.cargo, a.area
            FROM relacion_ente_persona rep
            LEFT JOIN ente e ON rep.enteid = e.enteid
            LEFT JOIN cargo c ON rep.cargoid = c.cargoid  
            LEFT JOIN area a ON rep.areaid = a.areaid
            WHERE rep.personaid = :persona_id
        """
        
        result = db.execute(text(query), {"persona_id": persona_id})
        relaciones = []
        
        for row in result.fetchall():
            relaciones.append({
                "id": row[0],
                "enteid": row[1], 
                "cargoid": row[2],
                "areaid": row[3],
                "empresa": row[4],
                "cargo": row[5],
                "area": row[6]
            })
            
        return {"relaciones": relaciones}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/persona/{persona_id}/relaciones/{relacion_id}")
async def delete_persona_relation(
    persona_id: int,
    relacion_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a relation between persona and empresa
    """
    try:
        query = "DELETE FROM relacion_ente_persona WHERE ente_persona_id = :relacion_id AND personaid = :persona_id"
        result = db.execute(text(query), {"relacion_id": relacion_id, "persona_id": persona_id})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Relación no encontrada")
            
        return {"message": "Relación eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consorcista")
async def create_consorcista_with_parcela(
    consorcista_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Create a new consorcista and optionally assign parcelas
    """
    try:
        # Create consorcista
        query = """
            INSERT INTO consorcista (nombre, nro_consorcista, tipoid, fecha_de_carga)
            VALUES (:nombre, :nro_consorcista, :tipoid, CURRENT_TIMESTAMP)
            RETURNING consorcistaid
        """
        
        result = db.execute(text(query), {
            "nombre": consorcista_data.get("nombre"),
            "nro_consorcista": consorcista_data.get("nro_consorcista"),
            "tipoid": consorcista_data.get("tipoid")
        })
        
        consorcista_id = result.fetchone()[0]
        
        # If parcela IDs provided, assign them
        parcela_ids = consorcista_data.get("parcela_ids", [])
        if parcela_ids:
            for parcela_id in parcela_ids:
                assign_query = "UPDATE parcela SET consorcistaid = :consorcista_id WHERE parcelaid = :parcela_id"
                db.execute(text(assign_query), {"consorcista_id": consorcista_id, "parcela_id": parcela_id})
        
        db.commit()
        
        return {
            "message": "Consorcista creado exitosamente",
            "consorcista_id": consorcista_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parcela")
async def create_parcela_with_consorcista(
    parcela_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Create a new parcela and optionally assign to consorcista
    """
    try:
        query = """
            INSERT INTO parcela (parcela, calle, numero, superficie_has_, 
                               consorcistaid, tieneplanta, alquilada, fecha_de_carga)
            VALUES (:parcela, :calle, :numero, :superficie_has, 
                    :consorcistaid, :tieneplanta, :alquilada, CURRENT_TIMESTAMP)
            RETURNING parcelaid
        """
        
        result = db.execute(text(query), {
            "parcela": parcela_data.get("parcela"),
            "calle": parcela_data.get("calle"),
            "numero": parcela_data.get("numero"),
            "superficie_has": parcela_data.get("superficie_has"),
            "consorcistaid": parcela_data.get("consorcistaid"),
            "tieneplanta": parcela_data.get("tieneplanta", False),
            "alquilada": parcela_data.get("alquilada", False)
        })
        
        parcela_id = result.fetchone()[0]
        db.commit()
        
        return {
            "message": "Parcela creada exitosamente",
            "parcela_id": parcela_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{table_name}/{record_id}")
async def get_record(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific record by ID
    """
    try:
        # Mock data for testing
        mock_record = {
            "id": record_id,
            "nombre": f"Registro {record_id}",
            "fecha": "2024-01-15",
            "estado": "Activo"
        }
        
        return mock_record
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{table_name}")
async def create_record(
    table_name: str,
    record_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new record
    """
    try:
        # For now, just return success with the provided data
        # In real implementation, this would insert into the database
        new_record = {"id": 999, **record_data}
        
        return {
            "message": "Record created successfully",
            "data": new_record
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{table_name}/{record_id}")
async def update_record(
    table_name: str,
    record_id: int,
    record_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing record
    """
    try:
        # For now, just return success
        # In real implementation, this would update the database record
        updated_record = {"id": record_id, **record_data}
        
        return {
            "message": "Record updated successfully",
            "data": updated_record
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{table_name}/{record_id}")
async def delete_record(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a record
    """
    try:
        # For now, just return success
        # In real implementation, this would delete the database record
        
        return {
            "message": "Record deleted successfully",
            "id": record_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/parcela/{parcela_id}/consorcista")
async def assign_parcela_to_consorcista(
    parcela_id: int,
    assignment_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Assign or unassign a parcela to/from a consorcista
    """
    try:
        consorcista_id = assignment_data.get("consorcistaid")
        
        if consorcista_id:
            query = "UPDATE parcela SET consorcistaid = :consorcista_id WHERE parcelaid = :parcela_id"
            db.execute(text(query), {"consorcista_id": consorcista_id, "parcela_id": parcela_id})
            message = "Parcela asignada al consorcista exitosamente"
        else:
            query = "UPDATE parcela SET consorcistaid = NULL WHERE parcelaid = :parcela_id"
            db.execute(text(query), {"parcela_id": parcela_id})
            message = "Parcela desasignada del consorcista exitosamente"
            
        db.commit()
        return {"message": message}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consorcista/{consorcista_id}/parcelas")
async def get_consorcista_parcelas(
    consorcista_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all parcelas assigned to a consorcista
    """
    try:
        query = """
            SELECT parcelaid, parcela, calle, numero, superficie_has_, 
                   tieneplanta, alquilada, fraccion
            FROM parcela 
            WHERE consorcistaid = :consorcista_id
            ORDER BY parcela
        """
        
        result = db.execute(text(query), {"consorcista_id": consorcista_id})
        parcelas = []
        
        for row in result.fetchall():
            parcelas.append({
                "id": row[0],
                "parcela": row[1],
                "calle": row[2],
                "numero": row[3],
                "superficie_has": row[4],
                "tieneplanta": row[5],
                "alquilada": row[6],
                "fraccion": row[7]
            })
            
        return {"parcelas": parcelas}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))