import json
from uuid import uuid4
from datetime import timezone
from sqlalchemy.orm import Session
from .models import Application, SignIn, Assignment, AppSession, IngestionBatch

CONFIG = {
    'applications': (Application, 'id', 'sp_id'),
    'signIns': (SignIn, 'id', 'event_id'),
    'appRoleAssignedTo': (Assignment, 'id', 'assignment_id'),
    'appSessions': (AppSession, 'sessionId', 'session_id'),
}

def ingest(db: Session, envelope):
    resource = envelope.resource
    model, incoming_key, db_key = CONFIG[resource]
    tenant = envelope.tenantId
    keys = [getattr(item, incoming_key) for item in envelope.value]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate IDs inside batch')
    inserted = updated = 0
    with db.begin():
        for item in envelope.value:
            payload = item.model_dump(mode='json')
            record = db.get(model, (tenant, getattr(item, incoming_key)))
            if record is None:
                record = model(tenant_id=tenant, **{db_key: getattr(item, incoming_key)})
                db.add(record)
                inserted += 1
            else:
                updated += 1
            record.raw_json = json.dumps(payload, ensure_ascii=False)
            if resource == 'applications':
                record.app_id, record.display_name, record.account_enabled = item.appId, item.displayName, item.accountEnabled
            elif resource == 'signIns':
                record.app_id, record.user_id = item.appId, item.userId
                record.occurred_at = item.createdDateTime.astimezone(timezone.utc).replace(tzinfo=None)
                record.error_code = item.status.errorCode
            elif resource == 'appRoleAssignedTo':
                record.resource_id, record.principal_id, record.principal_type = item.resourceId, item.principalId, item.principalType
            else:
                record.app_id, record.user_id = item.appId, item.userId
                record.started_at = item.startedAt.astimezone(timezone.utc).replace(tzinfo=None)
                record.ended_at = item.endedAt.astimezone(timezone.utc).replace(tzinfo=None)
                record.active_seconds, record.idle_seconds = item.activeSeconds, item.idleSeconds
        batch = IngestionBatch(batch_id=str(uuid4()), tenant_id=tenant, resource=resource, source=envelope.source, status='completed', inserted_count=inserted, updated_count=updated, rejected_count=0)
        db.add(batch)
    return {'batchId': batch.batch_id, 'inserted': inserted, 'updated': updated, 'rejected': 0}
