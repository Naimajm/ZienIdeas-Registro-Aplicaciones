from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import Envelope, SignInIn, SessionIn
from ..ingestion import ingest

router = APIRouter(tags=['activity'])

@router.post('/api/ingest/signins')
def ingest_signins(data: Envelope[SignInIn], db: Session = Depends(get_db)):
    if data.resource != 'signIns':
        raise HTTPException(422, 'Expected signIns')
    try:
        return ingest(db, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post('/api/ingest/sessions')
def ingest_sessions(data: Envelope[SessionIn], db: Session = Depends(get_db)):
    if data.resource != 'appSessions' or data.source != 'telemetry_mock':
        raise HTTPException(422, 'Expected appSessions from telemetry_mock')
    try:
        return ingest(db, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
