from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.data import BulkData
from app.schemas.upload import BulkDataSchema

router = APIRouter()

@router.get("/data", response_model=List[BulkDataSchema])
def get_all_data(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Devuelve todos los registros cargados (paginado)
    """
    records = db.query(BulkData).order_by(BulkData.created_at.desc()).offset(offset).limit(limit).all()
    return [BulkDataSchema.model_validate(r).model_dump() for r in records]


@router.get("/data/batch/{batch_id}", response_model=List[BulkDataSchema])
def get_data_by_batch(
    batch_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Devuelve los registros de un batch específico (paginado)
    """
    records = db.query(BulkData).filter(BulkData.batch_id == batch_id).order_by(BulkData.id).offset(offset).limit(limit).all()
    if not records:
        raise HTTPException(status_code=404, detail="No se encontraron registros para este batch")
    return [BulkDataSchema.model_validate(r).model_dump() for r in records]
