# CEPIP Web Application

Sistema de gestión CEPIP migrado desde Microsoft Access a aplicación web moderna.

## 🏗️ Arquitectura

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: FastAPI (Python) 
- **Base de datos**: PostgreSQL
- **Despliegue**: Railway

## 🚀 Despliegue en Railway 

### 1. Preparación

1. Crear cuenta en [Railway](https://railway.app)
2. Conectar cuenta de GitHub  
3. Configurar Google OAuth (ver sección OAuth)
4. Hacer fork/clone de este repositorio

### 2. Desplegar

1. En Railway: "New Project" → "Deploy from GitHub repo"
2. Seleccionar este repositorio
3. Railway detectará automáticamente el `Dockerfile`
4. Se creará automáticamente una base PostgreSQL

### 3. Configurar Variables de Entorno

Railway configurará automáticamente:
- `DATABASE_URL` → URL de PostgreSQL
- `PORT` → Puerto del servidor

Variables **requeridas**:
- `SECRET_KEY` → Clave secreta para JWT (generar una fuerte)
- `GOOGLE_CLIENT_ID` → Client ID de Google OAuth (ver sección OAuth)

Variables adicionales (opcional):
- `CORS_ORIGINS` → Dominios permitidos para CORS

### 4. Migrar Datos

Una vez desplegado, ejecutar desde el dashboard de Railway:

```bash
python migrate_to_production.py
```

## 🛠️ Desarrollo Local

### Requisitos

- Python 3.9+
- PostgreSQL 12+
- Docker (opcional)

### Instalación

```bash
# Clonar repositorio
git clone <url-del-repo>
cd cepip-web

# Instalar dependencias
pip install -r backend/requirements.txt

# Configurar base de datos
cp .env.example backend/.env
# Editar backend/.env con tus credenciales

# Ejecutar migraciones
python migrate_data_mdb.py

# Iniciar aplicación
cd backend
python main.py
```

La aplicación estará disponible en http://localhost:8000

## 📊 Funcionalidades

- ✅ Gestión de Personas con relaciones empresa-cargo
- ✅ Gestión de Consorcistas con parcelas asignadas  
- ✅ Gestión de Empresas con sectores/rubros
- ✅ Gestión de Parcelas con asignación de consorcistas
- ✅ Paginación y filtros en todas las secciones
- ✅ Exportación de datos a CSV
- ✅ Sistema de relaciones completo

## 📁 Estructura

```
cepip-web/
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── routes/    # Endpoints de la API
│   │   └── database.py
│   ├── main.py        # Aplicación principal
│   └── requirements.txt
├── frontend/          # Aplicación web
│   ├── js/           # JavaScript modules
│   ├── styles/       # CSS
│   └── index.html
├── Dockerfile         # Configuración Docker
├── railway.toml       # Configuración Railway
└── migrate_*.py       # Scripts de migración
```

## 🔗 API Endpoints

- `GET /api/records/{table}` - Listar registros con paginación
- `GET /api/records/lookup/*` - Datos para dropdowns
- `POST /api/records/persona/{id}/relaciones` - Crear relaciones
- `PUT /api/records/parcela/{id}/consorcista` - Asignar parcela
- `GET /docs` - Documentación interactiva de la API

## 📈 Migración desde Access

Los datos originales de Microsoft Access fueron migrados usando:

1. **mdb-tools** para extraer datos
2. **Scripts Python** para transformar y cargar
3. **PostgreSQL** como base de datos de destino
4. **Verificación** de integridad de datos

Total migrado: **3,847 registros** en **20 tablas**

## 🔐 Configuración Google OAuth

### 1. Crear Proyecto en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com)
2. Crear un nuevo proyecto o seleccionar uno existente
3. Habilitar **Google+ API** y **Google Identity Services**

### 2. Configurar OAuth 2.0

1. **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
2. **Application type**: Web application
3. **Name**: CEPIP Web App
4. **Authorized redirect URIs**:
   - `https://your-app.railway.app` (URL de Railway)
   - `http://localhost:8000` (desarrollo local)

### 3. Obtener Client ID

1. Copiar el **Client ID** (termina en `.googleusercontent.com`)
2. En Railway: **Variables** → Agregar `GOOGLE_CLIENT_ID`
3. Para desarrollo local: agregar a `.env`

### 4. Configurar Dominio Autorizado

En Google Cloud Console:
1. **OAuth consent screen**
2. **Authorized domains**: agregar `railway.app` y `localhost`

## 🛡️ Seguridad y Permisos

- ✅ **Primer usuario** se convierte automáticamente en **administrador**
- ✅ **Solo usuarios con Google** pueden acceder
- ✅ **JWT tokens** con expiración configurada
- ✅ **Middleware de autenticación** en todas las rutas protegidas
- ✅ **Validación de tokens** en frontend y backend

## 👤 Gestión de Usuarios

- **Login**: Solo con cuenta Google
- **Logout**: Limpia tokens locales
- **Roles**: Usuario normal / Administrador
- **Primer usuario**: Se convierte en admin automáticamente
