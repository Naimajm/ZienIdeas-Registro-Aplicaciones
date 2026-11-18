from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import AppSession, Application

def statistics(db: Session, tenant_id: str, day: date, app_id: str | None = None):
    start = datetime.combine(day, datetime.min.time())
    end = start + timedelta(days=1)
    query = select(AppSession).where(AppSession.tenant_id == tenant_id, AppSession.started_at >= start, AppSession.started_at < end)
    if app_id is not None:
        query = query.where(AppSession.app_id == app_id)
    sessions = db.scalars(query).all()
    names = {x.app_id: x.display_name for x in db.scalars(select(Application).where(Application.tenant_id == tenant_id)).all()}
    result = {}
    for s in sessions:
        x = result.setdefault(s.app_id, {'appId': s.app_id, 'displayName': names.get(s.app_id, s.app_id), 'sessionCount': 0, 'sessionSeconds': 0, 'activeSeconds': 0, 'idleSeconds': 0})
        x['sessionCount'] += 1
        x['activeSeconds'] += s.active_seconds
        x['idleSeconds'] += s.idle_seconds
        x['sessionSeconds'] += s.active_seconds + s.idle_seconds
    for x in result.values():
        x['activePercentage'] = round(100 * x['activeSeconds'] / x['sessionSeconds'], 2) if x['sessionSeconds'] else None
    return {'date': day.isoformat(), 'timezone': 'UTC', 'source': 'telemetry_mock', 'applications': sorted(result.values(), key=lambda x: x['appId'])}
