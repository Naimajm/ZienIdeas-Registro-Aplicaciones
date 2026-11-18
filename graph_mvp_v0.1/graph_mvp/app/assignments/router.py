from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import Envelope, AssignmentIn
from ..ingestion import ingest

router = APIRouter(tags=['assignments'])

@router.post('/api/ingest/assignments')
def ingest_assignments(data: Envelope[AssignmentIn], db: Session = Depends(get_db)):
    if data.resource != 'appRoleAssignedTo':
        raise HTTPException(422, 'Expected appRoleAssignedTo')
    try:
        return ingest(db, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
