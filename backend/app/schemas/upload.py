# schemas/upload.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class BulkDataSchema(BaseModel):
    """Schema para un registro individual"""
    nombre: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    valor: Optional[float] = None
    descripcion: Optional[str] = None
    
    class Config:
        from_attributes = True


class UploadInitResponse(BaseModel):
    """Respuesta al iniciar un cargue"""
    batch_id: str
    message: str


class ProgressUpdate(BaseModel):
    """Actualización de progreso (enviada por WebSocket)"""
    batch_id: str
    processed: int
    total: int
    successful: int
    failed: int
    percentage: float
    status: str  # processing, completed, failed
    current_record: Optional[str] = None
    estimated_time_remaining: Optional[float] = None
    speed: float  # registros por segundo


class UploadSummary(BaseModel):
    """Resumen final de cargue"""
    batch_id: str
    filename: str
    total_records: int
    successful_records: int
    failed_records: int
    status: str
    errors: List[dict] = []
    completed_at: datetime
    duration_seconds: float
    
    class Config:
        from_attributes = True


class ErrorDetail(BaseModel):
    """Detalle de error en un registro"""
    row_number: int
    error: str
    data: Optional[dict] = None