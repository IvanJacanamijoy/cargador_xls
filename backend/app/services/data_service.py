from sqlalchemy.orm import Session
from app.models.data import BulkData, UploadLog
from app.schemas.upload import BulkDataSchema
from typing import List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataService:
    """Servicio para insertar datos en la BD"""
    
    @staticmethod
    def create_upload_log(db: Session, batch_id: str, filename: str, 
                         total_records: int) -> UploadLog:
        """Crea registro de log del cargue"""
        upload_log = UploadLog(
            batch_id=batch_id,
            filename=filename,
            total_records=total_records,
            status="processing"
        )
        db.add(upload_log)
        db.commit()
        db.refresh(upload_log)
        return upload_log
    
    @staticmethod
    def insert_records(db: Session, batch_id: str, records: List[dict], 
                      chunk_size: int = 500) -> Tuple[int, int]:
        """
        Inserta registros en lotes
        Retorna (exitosos, fallidos)
        """
        successful = 0
        failed = 0
        
        try:
            # Procesar en chunks
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                
                try:
                    for record in chunk:
                        try:
                            # Validar schema
                            validated = BulkDataSchema(**record)
                            
                            # Crear objeto
                            bulk_data = BulkData(
                                batch_id=batch_id,
                                nombre=validated.nombre,
                                email=validated.email,
                                telefono=validated.telefono,
                                valor=validated.valor,
                                descripcion=validated.descripcion
                            )
                            db.add(bulk_data)
                            successful += 1
                            
                        except Exception as e:
                            logger.warning(f"Error validando registro: {e}")
                            failed += 1
                    
                    # Commit por lote
                    db.commit()
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error en chunk: {e}")
                    failed += len(chunk) - successful
            
        except Exception as e:
            logger.error(f"Error insertando registros: {e}")
            db.rollback()
            raise
        
        return successful, failed
    
    @staticmethod
    def update_upload_log(db: Session, batch_id: str, successful: int, 
                         failed: int, status: str, error_msg: str = None):
        """Actualiza el registro de log"""
        try:
            upload_log = db.query(UploadLog).filter(
                UploadLog.batch_id == batch_id
            ).first()
            
            if upload_log:
                upload_log.successful_records = successful
                upload_log.failed_records = failed
                upload_log.status = status
                upload_log.completed_at = datetime.now()
                if error_msg:
                    upload_log.error_message = error_msg
                
                db.commit()
                logger.info(f"Log actualizado para batch {batch_id}")
        
        except Exception as e:
            logger.error(f"Error actualizando log: {e}")
            db.rollback()
    
    @staticmethod
    def get_upload_log(db: Session, batch_id: str) -> UploadLog:
        """Obtiene el log de un cargue"""
        return db.query(UploadLog).filter(
            UploadLog.batch_id == batch_id
        ).first()
    
    @staticmethod
    def get_recent_uploads(db: Session, limit: int = 10) -> List[UploadLog]:
        """Obtiene los cargues más recientes"""
        return db.query(UploadLog).order_by(
            UploadLog.created_at.desc()
        ).limit(limit).all()