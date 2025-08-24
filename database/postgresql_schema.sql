-- PostgreSQL schema generated from Access database via mdbtools
-- Generated on: 2025-08-23 12:26:18

-- Table: AREA (21 records)
CREATE TABLE IF NOT EXISTS area (
    areaid SERIAL PRIMARY KEY,
    area VARCHAR(255)
);

-- Table: CAMARA (45 records)
CREATE TABLE IF NOT EXISTS camara (
    camaraid SERIAL PRIMARY KEY,
    abreviatura VARCHAR(255),
    camara VARCHAR(255)
);

-- Table: CARGO (284 records)
CREATE TABLE IF NOT EXISTS cargo (
    cargoid SERIAL PRIMARY KEY,
    cargo VARCHAR(255)
);

-- Table: CONSORCISTA (205 records)
CREATE TABLE IF NOT EXISTS consorcista (
    consorcistaid SERIAL PRIMARY KEY,
    nombre VARCHAR(255),
    nro_consorcista INTEGER NOT NULL,
    tipoid INTEGER NOT NULL,
    fecha_de_carga DATE
);

-- Table: ENTE (333 records)
CREATE TABLE IF NOT EXISTS ente (
    enteid SERIAL PRIMARY KEY,
    nro_socio_cepip INTEGER,
    razonsocial VARCHAR(255),
    cuit INTEGER,
    observaciones TEXT,
    web VARCHAR(255),
    consorcistaid INTEGER,
    actividadprincipalid INTEGER,
    actividadsecundariaid INTEGER,
    fecha_de_carga DATE,
    esconsorcista BOOLEAN NOT NULL,
    es_socio BOOLEAN NOT NULL
);

-- Table: ANOTACIONES (1 records)
CREATE TABLE IF NOT EXISTS anotaciones (
    anotacionid INTEGER,
    fecha_de_carga DATE,
    personaid INTEGER,
    enteid INTEGER,
    anotacion TEXT,
    fecha_limite DATE
);

-- Table: PARCELA (319 records)
CREATE TABLE IF NOT EXISTS parcela (
    parcelaid SERIAL PRIMARY KEY,
    parcela VARCHAR(255),
    calle VARCHAR(255),
    numero INTEGER,
    superficie_has INTEGER,
    porcentaje_reglamento INTEGER,
    consorcistaid INTEGER,
    fraccion VARCHAR(255),
    tieneplanta BOOLEAN NOT NULL,
    alquilada BOOLEAN NOT NULL,
    fecha_de_carga TIMESTAMP,
    enteid INTEGER
);

-- Table: PARCELA_ALQUILADA (4 records)
CREATE TABLE IF NOT EXISTS parcela_alquilada (
    alquilerid INTEGER,
    enteid INTEGER,
    parcelaid INTEGER,
    fecha_de_carga DATE
);

-- Table: PERSONA (989 records)
CREATE TABLE IF NOT EXISTS persona (
    personaid SERIAL PRIMARY KEY,
    fecha_de_carga TIMESTAMP,
    nombre_apellido VARCHAR(255),
    telefono VARCHAR(255),
    celular VARCHAR(255),
    correo_electronico VARCHAR(255),
    consorcistaid INTEGER
);

-- Table: RELACION_ENTE_CAMARA (46 records)
CREATE TABLE IF NOT EXISTS relacion_ente_camara (
    ente_camara_id INTEGER,
    enteid INTEGER,
    camaraid INTEGER,
    fecha_de_carga DATE
);

-- Table: RELACION_ENTE_PERSONA (991 records)
CREATE TABLE IF NOT EXISTS relacion_ente_persona (
    ente_persona_id INTEGER,
    enteid INTEGER,
    personaid INTEGER,
    cargoid INTEGER,
    areaid INTEGER,
    fecha_de_carga DATE
);

-- Table: RELACION_ENTE_SINDICATO (4 records)
CREATE TABLE IF NOT EXISTS relacion_ente_sindicato (
    ente_sindicato_id INTEGER,
    enteid INTEGER,
    sindicatoid INTEGER,
    fecha_de_carga DATE
);

-- Table: RUBRO (89 records)
CREATE TABLE IF NOT EXISTS rubro (
    rubroid SERIAL PRIMARY KEY NOT NULL,
    sectorid INTEGER,
    rubro VARCHAR(255)
);

-- Table: SECTOR (18 records)
CREATE TABLE IF NOT EXISTS sector (
    sectorid SERIAL PRIMARY KEY,
    sector VARCHAR(255)
);

-- Table: SINDICATO (61 records)
CREATE TABLE IF NOT EXISTS sindicato (
    sindicatoid SERIAL PRIMARY KEY,
    siglas VARCHAR(255),
    sindicato VARCHAR(255)
);

-- Table: SUBRUBRO (169 records)
CREATE TABLE IF NOT EXISTS subrubro (
    subrubroid SERIAL PRIMARY KEY,
    rubroid INTEGER,
    sub_numero INTEGER,
    subrubro VARCHAR(255)
);

-- Table: TIPO_CONSORCISTA (2 records)
CREATE TABLE IF NOT EXISTS tipo_consorcista (
    tipoconsorcistaid INTEGER,
    tipo VARCHAR(255)
);

-- Table: CALLE (25 records)
CREATE TABLE IF NOT EXISTS calle (
    calleid SERIAL PRIMARY KEY,
    calle VARCHAR(255)
);

-- Table: ACCESOS_ENTE (241 records)
CREATE TABLE IF NOT EXISTS accesos_ente (
    accesoid INTEGER,
    enteid INTEGER NOT NULL,
    calleid INTEGER NOT NULL,
    altura INTEGER,
    fecha_de_carga DATE
);

-- Table: CONDOMINO (0 records)
CREATE TABLE IF NOT EXISTS condomino (
    condominoid SERIAL PRIMARY KEY,
    personaunoid INTEGER,
    personadosid INTEGER,
    consorcistaid INTEGER
);
