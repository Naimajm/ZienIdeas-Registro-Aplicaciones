from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import IngestionBatch
from .applications.router import router as applications_router
from .activity.router import router as activity_router
from .assignments.router import router as assignments_router
from .analytics.router import router as analytics_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title='Microsoft Graph Analytics MVP', version='0.1.0')
for router in [applications_router, activity_router, assignments_router, analytics_router]:
    app.include_router(router)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/api/ingestion/batches')
def batches(tenant_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(select(IngestionBatch).where(IngestionBatch.tenant_id == tenant_id).order_by(IngestionBatch.received_at.desc())).all()
    return [{'batchId': x.batch_id, 'resource': x.resource, 'source': x.source, 'status': x.status, 'inserted': x.inserted_count, 'updated': x.updated_count} for x in rows]
