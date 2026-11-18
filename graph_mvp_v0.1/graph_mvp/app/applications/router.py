from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import Application
from ..schemas import Envelope, ApplicationIn
from ..ingestion import ingest

router = APIRouter(tags=['applications'])

@router.post('/api/ingest/applications')
def ingest_applications(data: Envelope[ApplicationIn], db: Session = Depends(get_db)):
    if data.resource != 'applications' and data.resource != 'servicePrincipals':
        raise HTTPException(422, 'Expected servicePrincipals')
    data.resource = 'applications'
    try:
        return ingest(db, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get('/api/applications')
def list_applications(tenant_id: str, db: Session = Depends(get_db)):
    items = db.scalars(select(Application).where(Application.tenant_id == tenant_id).order_by(Application.display_name)).all()
    return [{'id': x.sp_id, 'appId': x.app_id, 'displayName': x.display_name, 'accountEnabled': x.account_enabled} for x in items]
