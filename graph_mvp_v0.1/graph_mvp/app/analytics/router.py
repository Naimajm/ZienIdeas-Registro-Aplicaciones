from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .service import statistics

router = APIRouter(tags=['analytics'])

@router.get('/api/statistics/applications')
def all_statistics(tenant_id: str, date: date, db: Session = Depends(get_db)):
    return statistics(db, tenant_id, date)

@router.get('/api/statistics/applications/{app_id}')
def app_statistics(app_id: str, tenant_id: str, date: date, db: Session = Depends(get_db)):
    return statistics(db, tenant_id, date, app_id)
