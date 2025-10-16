from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date, datetime
from typing import List


class BulkDataSchema(BaseModel):
    batch_id: str
    codigo_cliente: Optional[str] = None  # ← reemplaza el campo 'id' del Excel
    nombre_completo: str = Field(..., min_length=1, max_length=255)
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[str] = None
    localidad_cp: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: EmailStr
    fecha_alta: Optional[date] = None
    grupo_clientes: Optional[str] = None
    valor: Optional[float] = None
    descripcion: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True



class UploadInitRequest(BaseModel):
    """Request para iniciar cargue"""
    filename: str


class UploadInitResponse(BaseModel):
    """Respuesta al iniciar cargue"""
    batch_id: str
    message: str


class ErrorDetail(BaseModel):
    """Detalle de error en un registro"""
    row_number: str
    error: str
    data: Optional[dict] = None


class UploadSummary(BaseModel):
    """Resumen final de cargue"""
    batch_id: str
    filename: str
    total_records: int
    successful_records: int
    failed_records: int
    status: str
    errors: List[ErrorDetail] = []
    completed_at: datetime
    duration_seconds: float

    class Config:
        orm_mode = True


class ProgressUpdate(BaseModel):
    """Actualización de progreso (para WebSocket o polling)"""
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
