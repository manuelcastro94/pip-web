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
    search: Optional[str] = Query(None, description="Search term"),
    es_socio: Optional[str] = Query(None, description="Filter by es_socio (true/false)"),
    esconsorcista: Optional[str] = Query(None, description="Filter by esconsorcista (true/false)"),
    con_email: Optional[str] = Query(None, description="Filter by has email (true/false)"),
    tieneplanta: Optional[str] = Query(None, description="Filter by tiene planta (true/false)"),
    alquilada: Optional[str] = Query(None, description="Filter by alquilada (true/false)"),
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
        
        # Build WHERE conditions based on filters
        where_conditions = []
        params = {"limit": limit, "offset": offset}
        
        def build_filters(table_name, search, es_socio, esconsorcista, con_email, tieneplanta, alquilada):
            conditions = []
            
            if table_name == 'ente':
                if search:
                    conditions.append("(e.razonsocial ILIKE :search OR CAST(e.cuit AS TEXT) ILIKE :search)")
                    params["search"] = f"%{search}%"
                if es_socio in ['true', 'false']:
                    conditions.append("e.es_socio = :es_socio")
                    params["es_socio"] = es_socio == 'true'
                if esconsorcista in ['true', 'false']:
                    conditions.append("e.esconsorcista = :esconsorcista")
                    params["esconsorcista"] = esconsorcista == 'true'
                    
            elif table_name == 'persona':
                if search:
                    conditions.append("(p.nombre_apellido ILIKE :search OR p.correo_electronico ILIKE :search OR p.telefono ILIKE :search)")
                    params["search"] = f"%{search}%"
                if con_email in ['true', 'false']:
                    if con_email == 'true':
                        conditions.append("(p.correo_electronico IS NOT NULL AND p.correo_electronico != '')")
                    else:
                        conditions.append("(p.correo_electronico IS NULL OR p.correo_electronico = '')")
                        
            elif table_name == 'consorcista':
                if search:
                    conditions.append("(c.nombre ILIKE :search OR CAST(c.nro_consorcista AS TEXT) ILIKE :search)")
                    params["search"] = f"%{search}%"
                    
            elif table_name == 'parcela':
                if search:
                    conditions.append("(p.parcela ILIKE :search OR p.calle ILIKE :search)")
                    params["search"] = f"%{search}%"
                if tieneplanta in ['true', 'false']:
                    conditions.append("p.tieneplanta = :tieneplanta")
                    params["tieneplanta"] = tieneplanta == 'true'
                if alquilada in ['true', 'false']:
                    conditions.append("p.alquilada = :alquilada")
                    params["alquilada"] = alquilada == 'true'
                    
            return " AND ".join(conditions)
        
        where_clause = build_filters(table_name, search, es_socio, esconsorcista, con_email, tieneplanta, alquilada)
        where_sql = f" WHERE {where_clause}" if where_clause else ""
        
        # Get total count with filters
        if table_name == 'ente':
            count_query = f"""
                SELECT COUNT(*) FROM ente e 
                LEFT JOIN subrubro sr ON e.actividadprincipalid = sr.subrubroid 
                LEFT JOIN rubro r ON sr.rubroid = r.rubroid 
                LEFT JOIN sector s ON r.sectorid = s.sectorid 
                {where_sql}
            """
        elif table_name == 'persona':
            count_query = f"SELECT COUNT(*) FROM persona p {where_sql}"
        elif table_name == 'consorcista':
            count_query = f"SELECT COUNT(*) FROM consorcista c {where_sql}"
        elif table_name == 'parcela':
            count_query = f"SELECT COUNT(*) FROM parcela p {where_sql}"
        else:
            count_query = f"SELECT COUNT(*) FROM {table_name} {where_sql}"
            
        count_result = db.execute(text(count_query), params)
        total = count_result.scalar()
        
        # Get paginated data with JOINs for better display
        if table_name == 'parcela':
            # Join with consorcista to get the name
            query = f"""
                SELECT p.*, c.nombre as consorcista_nombre 
                FROM parcela p 
                LEFT JOIN consorcista c ON p.consorcistaid = c.consorcistaid 
                {where_sql}
                ORDER BY p.parcelaid 
                LIMIT :limit OFFSET :offset
            """
        elif table_name == 'ente':
            # Join with sector and rubro for empresas (through subrubro)
            query = f"""
                SELECT e.*, s.sector as sector_nombre, r.rubro as rubro_nombre, sr.subrubro as subrubro_nombre
                FROM ente e 
                LEFT JOIN subrubro sr ON e.actividadprincipalid = sr.subrubroid 
                LEFT JOIN rubro r ON sr.rubroid = r.rubroid 
                LEFT JOIN sector s ON r.sectorid = s.sectorid 
                {where_sql}
                ORDER BY e.enteid 
                LIMIT :limit OFFSET :offset
            """
        elif table_name == 'persona':
            # Join with relaciones to get empresas and cargos
            having_clause = ""
            if where_clause:
                # For persona, we need to use HAVING instead of WHERE because of GROUP BY
                having_clause = f" HAVING {where_clause.replace('WHERE ', '')}"
                where_sql = ""  # Clear WHERE since we use HAVING
            
            query = f"""
                SELECT p.*, 
                       STRING_AGG(DISTINCT e.razonsocial, ', ' ORDER BY e.razonsocial) as empresas,
                       STRING_AGG(DISTINCT c.cargo, ', ' ORDER BY c.cargo) as cargos
                FROM persona p 
                LEFT JOIN relacion_ente_persona rep ON p.personaid = rep.personaid 
                LEFT JOIN ente e ON rep.enteid = e.enteid 
                LEFT JOIN cargo c ON rep.cargoid = c.cargoid 
                GROUP BY p.personaid, p.fecha_de_carga, p.nombre_apellido, p.telefono, p.celular, p.correo_electronico, p.consorcistaid
                {having_clause}
                ORDER BY p.personaid 
                LIMIT :limit OFFSET :offset
            """
        elif table_name == 'consorcista':
            # Join with tipo and count parcelas/empresas
            having_clause = ""
            if where_clause:
                # For consorcista, we need to use HAVING instead of WHERE because of GROUP BY
                having_clause = f" HAVING {where_clause.replace('WHERE ', '')}"
                where_sql = ""  # Clear WHERE since we use HAVING
                
            query = f"""
                SELECT c.*, 
                       tc.tipo as tipo_nombre,
                       COUNT(DISTINCT p.parcelaid) as parcelas_count,
                       COUNT(DISTINCT e.enteid) as empresas_count
                FROM consorcista c 
                LEFT JOIN tipo_consorcista tc ON c.tipoid = tc.tipoconsorcistaid 
                LEFT JOIN parcela p ON c.consorcistaid = p.consorcistaid 
                LEFT JOIN ente e ON c.consorcistaid = e.consorcistaid 
                GROUP BY c.consorcistaid, c.nombre, c.nro_consorcista, c.tipoid, c.fecha_de_carga, tc.tipo
                {having_clause}
                ORDER BY c.consorcistaid 
                LIMIT :limit OFFSET :offset
            """
        else:
            query = f"SELECT * FROM {table_name} {where_sql} ORDER BY 1 LIMIT :limit OFFSET :offset"
        
        result = db.execute(text(query), params)
        
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
        # Validate table name to prevent SQL injection
        valid_tables = ['ente', 'persona', 'consorcista', 'parcela']
        if table_name not in valid_tables:
            raise HTTPException(status_code=404, detail="Table not found")
        
        if table_name == 'ente':
            # Get next available ID
            next_id_result = db.execute(text("SELECT COALESCE(MAX(enteid), 0) + 1 FROM ente"))
            next_id = next_id_result.scalar()
            
            # Create empresa/ente
            query = """
                INSERT INTO ente (enteid, razonsocial, cuit, nro_socio_cepip, web, observaciones, 
                                 es_socio, esconsorcista, actividadprincipalid, actividadsecundariaid, 
                                 consorcistaid, fecha_de_carga)
                VALUES (:enteid, :razonsocial, :cuit, :nro_socio_cepip, :web, :observaciones,
                        :es_socio, :esconsorcista, :actividadprincipalid, :actividadsecundariaid,
                        :consorcistaid, CURRENT_DATE)
            """
            
            db.execute(text(query), {
                "enteid": next_id,
                "razonsocial": record_data.get("razonsocial"),
                "cuit": record_data.get("cuit"),
                "nro_socio_cepip": record_data.get("nro_socio_cepip"),
                "web": record_data.get("web"),
                "observaciones": record_data.get("observaciones"),
                "es_socio": record_data.get("es_socio", False),
                "esconsorcista": record_data.get("esconsorcista", False),
                "actividadprincipalid": record_data.get("actividadprincipalid"),
                "actividadsecundariaid": record_data.get("actividadsecundariaid"),
                "consorcistaid": record_data.get("consorcistaid")
            })
            
            new_id = next_id
            db.commit()
            
            return {
                "message": "Empresa creada exitosamente",
                "data": {"enteid": new_id, **record_data}
            }
            
        elif table_name == 'persona':
            print(f"🔍 Backend: Creating persona with data: {record_data}")
            
            # Get next available ID for persona
            next_id_result = db.execute(text("SELECT COALESCE(MAX(personaid), 0) + 1 FROM persona"))
            next_id = next_id_result.scalar()
            print(f"🔍 Backend: Next persona ID will be: {next_id}")
            
            # Create persona
            query = """
                INSERT INTO persona (personaid, nombre_apellido, telefono, celular, 
                                   correo_electronico, consorcistaid, fecha_de_carga)
                VALUES (:personaid, :nombre_apellido, :telefono, :celular,
                        :correo_electronico, :consorcistaid, CURRENT_DATE)
            """
            
            print(f"🔍 Backend: Executing INSERT for persona with ID: {next_id}")
            db.execute(text(query), {
                "personaid": next_id,
                "nombre_apellido": record_data.get("nombre_apellido"),
                "telefono": record_data.get("telefono"),
                "celular": record_data.get("celular"),
                "correo_electronico": record_data.get("correo_electronico"),
                "consorcistaid": record_data.get("consorcistaid")
            })
            
            db.commit()
            print(f"🔍 Backend: Persona {next_id} created successfully")
            
            return {
                "message": "Persona creada exitosamente",
                "data": {"personaid": next_id, **record_data}
            }
            
        elif table_name == 'parcela':
            # Create parcela (has auto-increment)
            query = """
                INSERT INTO parcela (parcela, calle, numero, superficie_has_, porcentaje_reglamento,
                                   consorcistaid, fraccion, tieneplanta, alquilada, enteid, fecha_de_carga)
                VALUES (:parcela, :calle, :numero, :superficie_has, :porcentaje_reglamento,
                        :consorcistaid, :fraccion, :tieneplanta, :alquilada, :enteid, CURRENT_DATE)
                RETURNING parcelaid
            """
            
            result = db.execute(text(query), {
                "parcela": record_data.get("parcela"),
                "calle": record_data.get("calle"),
                "numero": record_data.get("numero"),
                "superficie_has": record_data.get("superficie_has"),
                "porcentaje_reglamento": record_data.get("porcentaje_reglamento"),
                "consorcistaid": record_data.get("consorcistaid"),
                "fraccion": record_data.get("fraccion"),
                "tieneplanta": record_data.get("tieneplanta", False),
                "alquilada": record_data.get("alquilada", False),
                "enteid": record_data.get("enteid")
            })
            
            new_id = result.fetchone()[0]
            db.commit()
            
            return {
                "message": "Parcela creada exitosamente",
                "data": {"parcelaid": new_id, **record_data}
            }
            
        elif table_name == 'consorcista':
            # Create consorcista (has auto-increment)
            query = """
                INSERT INTO consorcista (nombre, nro_consorcista, tipoid, fecha_de_carga)
                VALUES (:nombre, :nro_consorcista, :tipoid, CURRENT_DATE)
                RETURNING consorcistaid
            """
            
            result = db.execute(text(query), {
                "nombre": record_data.get("nombre"),
                "nro_consorcista": record_data.get("nro_consorcista"),
                "tipoid": record_data.get("tipoid")
            })
            
            new_id = result.fetchone()[0]
            db.commit()
            
            return {
                "message": "Consorcista creado exitosamente",
                "data": {"consorcistaid": new_id, **record_data}
            }
        else:
            # For other tables, return a placeholder for now
            new_record = {"id": 999, **record_data}
            
            return {
                "message": f"Record created successfully in {table_name}",
                "data": new_record
            }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
        # Map table names to actual table names and their ID columns
        table_mapping = {
            "ente": ("ente", "enteid"),
            "persona": ("persona", "personaid"),
            "consorcista": ("consorcista", "consorcistaid"),
            "parcela": ("parcela", "parcelaid"),
            "sector": ("sector", "sectorid")
        }
        
        if table_name not in table_mapping:
            raise HTTPException(status_code=400, detail=f"Table '{table_name}' not supported")
        
        actual_table, id_column = table_mapping[table_name]
        
        # First check if record exists
        check_query = f"SELECT 1 FROM {actual_table} WHERE {id_column} = :record_id"
        result = db.execute(text(check_query), {"record_id": record_id})
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
        
        # Delete the record
        delete_query = f"DELETE FROM {actual_table} WHERE {id_column} = :record_id"
        result = db.execute(text(delete_query), {"record_id": record_id})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
        
        return {
            "message": "Record deleted successfully",
            "id": record_id,
            "table": actual_table
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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

# ========== NUEVAS RELACIONES ==========

@router.get("/ente/{ente_id}/direcciones")
async def get_ente_direcciones(
    ente_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all direcciones (accesos) for an ente
    """
    try:
        query = """
            SELECT ae.accesoid, c.calle, ae.altura, ae.fecha_de_carga
            FROM accesos_ente ae
            JOIN calle c ON ae.calleid = c.calleid
            WHERE ae.enteid = :ente_id
            ORDER BY c.calle, ae.altura
        """
        
        result = db.execute(text(query), {"ente_id": ente_id})
        direcciones = []
        
        for row in result.fetchall():
            direcciones.append({
                "id": row[0],
                "calle": row[1],
                "altura": row[2],
                "fecha_de_carga": row[3]
            })
            
        return {"direcciones": direcciones}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ente/{ente_id}/camaras")
async def get_ente_camaras(
    ente_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all camaras for an ente
    """
    try:
        query = """
            SELECT rec.ente_camara_id, c.camara, rec.fecha_de_carga
            FROM relacion_ente_camara rec
            JOIN camara c ON rec.camaraid = c.camaraid
            WHERE rec.enteid = :ente_id
            ORDER BY c.camara
        """
        
        result = db.execute(text(query), {"ente_id": ente_id})
        camaras = []
        
        for row in result.fetchall():
            camaras.append({
                "id": row[0],
                "camara": row[1],
                "fecha_de_carga": row[2]
            })
            
        return {"camaras": camaras}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ente/{ente_id}/sindicatos")
async def get_ente_sindicatos(
    ente_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all sindicatos for an ente
    """
    try:
        query = """
            SELECT res.ente_sindicato_id, s.siglas, s.sindicato, res.fecha_de_carga
            FROM relacion_ente_sindicato res
            JOIN sindicato s ON res.sindicatoid = s.sindicatoid
            WHERE res.enteid = :ente_id
            ORDER BY s.sindicato
        """
        
        result = db.execute(text(query), {"ente_id": ente_id})
        sindicatos = []
        
        for row in result.fetchall():
            sindicatos.append({
                "id": row[0],
                "siglas": row[1],
                "sindicato": row[2],
                "fecha_de_carga": row[3]
            })
            
        return {"sindicatos": sindicatos}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/camaras")
async def get_camaras_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get all camaras for dropdown
    """
    try:
        query = "SELECT camaraid, camara FROM camara ORDER BY camara"
        result = db.execute(text(query))
        camaras = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"camaras": camaras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/sindicatos")
async def get_sindicatos_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get all sindicatos for dropdown
    """
    try:
        query = "SELECT sindicatoid, siglas, sindicato FROM sindicato ORDER BY sindicato"
        result = db.execute(text(query))
        sindicatos = [{"id": row[0], "siglas": row[1], "name": row[2]} for row in result.fetchall()]
        return {"sindicatos": sindicatos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lookup/calles")
async def get_calles_lookup(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Get all calles for dropdown
    """
    try:
        query = "SELECT calleid, calle FROM calle ORDER BY calle"
        result = db.execute(text(query))
        calles = [{"id": row[0], "name": row[1]} for row in result.fetchall()]
        return {"calles": calles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))