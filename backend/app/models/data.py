from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Date, func
from app.database import Base

class BulkData(Base):
    __tablename__ = "bulk_data"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), index=True, nullable=False)

    codigo_cliente = Column(String(20), nullable=True)  # ← nuevo campo
    nombre_completo = Column(String(255))
    fecha_nacimiento = Column(Date, nullable=True)
    direccion = Column(String(255), nullable=True)
    localidad_cp = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    fecha_alta = Column(Date, nullable=True)
    grupo_clientes = Column(String(100), nullable=True)

    valor = Column(Float, nullable=True)
    descripcion = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<BulkData(id={self.id}, batch_id={self.batch_id}, nombre_completo={self.nombre_completo})>"
