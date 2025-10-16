from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class BulkData(Base):
    """
    Modelo para almacenar datos cargados desde XLS
    Ajusta según tus necesidades reales
    """
    __tablename__ = "bulk_data"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), index=True, nullable=False)  # ID del cargue
    
    # Campos de ejemplo (ajusta a tu caso real)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    telefono = Column(String(20), nullable=True)
    valor = Column(Float, nullable=True)
    descripcion = Column(Text, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BulkData(id={self.id}, batch_id={self.batch_id}, nombre={self.nombre})>"


class UploadLog(Base):
    """
    Registro de cada cargue realizado
    """
    __tablename__ = "upload_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    total_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<UploadLog(batch_id={self.batch_id}, status={self.status})>"