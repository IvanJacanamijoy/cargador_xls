from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.api.routes import router as routes_router
from app.api.websocket import router as websocket_router
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app
app = FastAPI(
    title="Bulk Upload API",
    description="API para cargue masivo de datos desde XLS a MySQL",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Inicializa la BD al iniciar la app"""
    try:
        init_db()
        logger.info("Aplicación iniciada correctamente")
    except Exception as e:
        logger.error(f"Error en startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al apagar la app"""
    logger.info("Aplicación apagada")

# Incluir routers
app.include_router(routes_router, prefix="/api", tags=["upload"])
app.include_router(websocket_router, tags=["websocket"])

# Root
@app.get("/")
async def root():
    return {
        "message": "Bienvenido a Bulk Upload API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )