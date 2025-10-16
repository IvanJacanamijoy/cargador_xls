# app/background/tasks.py
from sqlalchemy.orm import Session
from app.models.data import BulkData
from app.services.progress_manager import progress_manager
from app.services.data_service import DataService
from app.database import SessionLocal
from app.utils.logger import get_logger
import logging

logger = get_logger(__name__)


async def process_batch_task(batch_id: str, valid_data: list, errors: list, 
                             file_path: str, chunk_size: int):
    """
    Tarea de background que procesa el batch
    Actualiza progreso para que WebSocket lo envíe a los clientes
    """
    db = SessionLocal()
    successful = 0
    failed = len(errors)
    
    try:
        # Procesar registros válidos
        for i, record in enumerate(valid_data):
            try:
                # Crear objeto
                bulk_data = BulkData(
                    batch_id=batch_id,
                    nombre=record.get("nombre"),
                    email=record.get("email"),
                    telefono=record.get("telefono"),
                    valor=record.get("valor"),
                    descripcion=record.get("descripcion")
                )
                db.add(bulk_data)
                successful += 1
                
                # Commit cada chunk_size
                if (i + 1) % chunk_size == 0:
                    db.commit()
                    logger.info(f"Batch {batch_id}: {i + 1}/{len(valid_data)} procesados")
                
                # Actualizar progreso
                await progress_manager.update_progress(
                    batch_id,
                    successful=1,
                    current_record=f"{record.get('nombre')} ({record.get('email')})"
                )
            
            except Exception as e:
                logger.warning(f"Error procesando registro {i}: {e}")
                failed += 1
                await progress_manager.update_progress(
                    batch_id,
                    failed=1,
                    error={
                        "row_number": i + 2,
                        "error": str(e),
                        "data": record
                    }
                )
        
        # Commit final
        db.commit()
        
        # Actualizar BD
        DataService.update_upload_log(
            db,
            batch_id,
            successful,
            failed,
            "completed"
        )
        
        # Marcar como completado
        await progress_manager.complete_batch(batch_id, "completed")
        logger.info(f"Batch {batch_id} completado: {successful} exitosos, {failed} fallidos")
    
    except Exception as e:
        logger.error(f"Error en process_batch_task: {e}")
        db.rollback()
        
        DataService.update_upload_log(
            db,
            batch_id,
            successful,
            failed,
            "failed",
            str(e)
        )
        
        await progress_manager.complete_batch(batch_id, "failed", str(e))
    
    finally:
        db.close()
        # Limpiar archivo (opcional, ya está en routes.py)
        import os
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo: {e}")


# app/utils/constants.py
"""Constantes de la aplicación"""

# Estados de cargue
UPLOAD_STATUS_PENDING = "pending"
UPLOAD_STATUS_PROCESSING = "processing"
UPLOAD_STATUS_COMPLETED = "completed"
UPLOAD_STATUS_FAILED = "failed"

UPLOAD_STATUSES = [
    UPLOAD_STATUS_PENDING,
    UPLOAD_STATUS_PROCESSING,
    UPLOAD_STATUS_COMPLETED,
    UPLOAD_STATUS_FAILED
]

# Tipos de WebSocket
WS_TYPE_PROGRESS = "progress"
WS_TYPE_COMPLETED = "completed"
WS_TYPE_ERROR = "error"
WS_TYPE_INITIAL = "initial"
WS_TYPE_STATUS = "status"
WS_TYPE_INFO = "info"

# Validación de archivos
ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
MAX_FILENAME_LENGTH = 255

# Campos de datos
REQUIRED_FIELDS = ["nombre", "email"]
OPTIONAL_FIELDS = ["telefono", "valor", "descripcion"]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

# Límites
DEFAULT_CHUNK_SIZE = 500
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB