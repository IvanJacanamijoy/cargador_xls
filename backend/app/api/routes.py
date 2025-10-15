from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.services.file_processor import FileProcessor
from app.services.data_service import DataService
from app.services.progress_manager import progress_manager
from app.schemas.upload import UploadInitResponse, UploadSummary
from app.utils.exceptions import (
    InvalidFileException, 
    FileTooLargeException,
    NoFileUploadedException
)
import uuid
import logging
import os
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload/init", response_model=UploadInitResponse)
async def init_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Inicia el proceso de cargue
    - Valida el archivo
    - Extrae datos
    - Retorna batch_id para seguimiento
    """
    settings = get_settings()
    
    # Validar que hay archivo
    if not file:
        raise NoFileUploadedException()
    
    # Validar extensión
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise InvalidFileException("Solo se aceptan archivos .xlsx o .xls")
    
    batch_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{batch_id}_{file.filename}")
    
    try:
        # Guardar archivo
        contents = await file.read()
        
        # Validar tamaño
        if len(contents) > settings.MAX_FILE_SIZE:
            max_mb = settings.MAX_FILE_SIZE // (1024 * 1024)
            raise FileTooLargeException(max_mb)
        
        # Escribir archivo
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Validar archivo
        FileProcessor.validate_file(file_path)
        
        # Extraer datos
        valid_data, errors = FileProcessor.extract_data(file_path)
        total_records = len(valid_data) + len(errors)
        
        logger.info(f"Batch {batch_id}: {len(valid_data)} válidos, {len(errors)} errores")
        
        # Inicializar tracking de progreso
        await progress_manager.init_batch(batch_id, total_records)
        
        # Crear log en BD
        DataService.create_upload_log(
            db, 
            batch_id, 
            file.filename, 
            total_records
        )
        
        return UploadInitResponse(
            batch_id=batch_id,
            message=f"Cargue iniciado. {total_records} registros detectados"
        )
    
    except Exception as e:
        logger.error(f"Error en init_upload: {e}")
        # Limpiar archivo
        if os.path.exists(file_path):
            os.remove(file_path)
        raise


@router.post("/upload/process/{batch_id}")
async def process_upload(
    batch_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Inicia el procesamiento en background
    Los WebSocket se conectarán para recibir actualizaciones
    """
    settings = get_settings()
    file_path = None
    
    try:
        # Buscar archivo
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(batch_id):
                file_path = os.path.join(UPLOAD_DIR, f)
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Cargue no encontrado")
        
        # Extraer datos
        valid_data, errors = FileProcessor.extract_data(file_path)
        
        # Agregar tarea de procesamiento al background
        background_tasks.add_task(
            process_batch_task,
            batch_id=batch_id,
            valid_data=valid_data,
            errors=errors,
            file_path=file_path,
            chunk_size=settings.CHUNK_SIZE
        )
        
        return {
            "message": "Procesamiento iniciado",
            "batch_id": batch_id,
            "total_records": len(valid_data) + len(errors)
        }
    
    except Exception as e:
        logger.error(f"Error en process_upload: {e}")
        await progress_manager.complete_batch(batch_id, "failed", str(e))
        raise


async def process_batch_task(batch_id: str, valid_data: list, errors: list, 
                             file_path: str, chunk_size: int):
    """
    Tarea de background que procesa el batch
    Actualiza progreso para que WebSocket lo envíe a los clientes
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    successful = 0
    failed = len(errors)
    
    try:
        # Procesar registros válidos en chunks
        for i, record in enumerate(valid_data):
            try:
                # Insertar registro
                from app.models.data import BulkData
                
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
        # Limpiar archivo
        if os.path.exists(file_path):
            os.remove(file_path)


@router.get("/upload/status/{batch_id}")
async def get_upload_status(batch_id: str):
    """Obtiene el estado actual de un cargue"""
    progress = progress_manager.get_progress(batch_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    
    return progress


@router.get("/uploads/recent")
async def get_recent_uploads(db: Session = Depends(get_db)):
    """Obtiene los cargues más recientes"""
    uploads = DataService.get_recent_uploads(db, limit=20)
    return uploads