from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.services.file_processor import FileProcessor
from app.schemas.upload import UploadInitResponse, UploadSummary
from app.models.data import BulkData
from app.services import progress_manager
from app.utils.exceptions import (
    InvalidFileException,
    FileTooLargeException,
    NoFileUploadedException,
    BatchNotFoundException
)
import uuid
import os
import time
from datetime import datetime

router = APIRouter()
settings = get_settings()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/upload/batches")
def get_batches(db: Session = Depends(get_db)):
    batches = db.query(BulkData.batch_id).distinct().all()
    return [{"batch_id": b[0]} for b in batches]


@router.get("/upload/status/{batch_id}")
async def get_upload_status(batch_id: str):
    """Obtiene el estado actual de un cargue"""
    progress = progress_manager.get_progress(batch_id)
    if not progress:
        raise BatchNotFoundException(batch_id)
    return progress


@router.post("/upload/init", response_model=UploadInitResponse)
async def init_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Guarda el archivo y valida su contenido
    """
    if not file:
        raise NoFileUploadedException()

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise InvalidFileException("Solo se aceptan archivos .xlsx o .xls")

    batch_id = str(uuid.uuid4())
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in ("_", ".", "-"))
    file_path = os.path.join(UPLOAD_DIR, f"{batch_id}_{safe_name}")

    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE // (1024 * 1024)
        raise FileTooLargeException(max_mb)

    with open(file_path, "wb") as f:
        f.write(contents)

    FileProcessor.validate_file(file_path)

    return UploadInitResponse(
        batch_id=batch_id,
        message="Archivo recibido y validado correctamente"
    )


@router.post("/upload/process/{batch_id}", response_model=UploadSummary)
async def process_upload(batch_id: str, db: Session = Depends(get_db)):
    """
    Procesa el archivo y guarda los registros válidos
    """
    start = time.time()
    file_path = None

    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(batch_id):
            file_path = os.path.join(UPLOAD_DIR, f)
            break

    if not file_path or not os.path.exists(file_path):
        raise BatchNotFoundException(batch_id)

    # Extraer y validar datos con batch_id incluido
    valid_data, errors = FileProcessor.extract_data(file_path, batch_id=batch_id)

    # Inicializar progreso
    await progress_manager.init_batch(batch_id, total=len(valid_data) + len(errors))

    successful = 0
    for record in valid_data:
        try:
            # Eliminar campos no insertables
            record.pop("created_at", None)
            record.pop("updated_at", None)

            db.add(BulkData(**record))
            successful += 1
            await progress_manager.update_progress(
                batch_id=batch_id,
                successful=1,
                current_record=record.get("email")
            )
        except Exception as e:
            error = ErrorDetail(
                row_number=record.get("codigo_cliente", "desconocido"),
                error=str(e),
                data=record
            )
            errors.append(error)
            await progress_manager.update_progress(
                batch_id=batch_id,
                failed=1,
                error=error.dict()
            )

    db.commit()
    await progress_manager.complete_batch(batch_id, status="completed")

    duration = time.time() - start

    return UploadSummary(
        batch_id=batch_id,
        filename=os.path.basename(file_path),
        total_records=len(valid_data) + len(errors),
        successful_records=successful,
        failed_records=len(errors),
        status="completed",
        errors=errors,
        completed_at=datetime.utcnow(),
        duration_seconds=round(duration, 2)
    )