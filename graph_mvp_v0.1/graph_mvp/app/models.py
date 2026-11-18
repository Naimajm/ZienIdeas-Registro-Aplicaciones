from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
from datetime import datetime, timezone

class Application(Base):
    __tablename__ = 'applications'
    tenant_id: Mapped[str] = mapped_column(String, primary_key=True)
    sp_id: Mapped[str] = mapped_column(String, primary_key=True)
    app_id: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str] = mapped_column(String)
    account_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)

class SignIn(Base):
    __tablename__ = 'sign_in_events'
    tenant_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    app_id: Mapped[str | None] = mapped_column(String, index=True)
    user_id: Mapped[str | None] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    error_code: Mapped[int] = mapped_column(Integer)
    raw_json: Mapped[str] = mapped_column(Text)

class Assignment(Base):
    __tablename__ = 'app_assignments'
    tenant_id: Mapped[str] = mapped_column(String, primary_key=True)
    assignment_id: Mapped[str] = mapped_column(String, primary_key=True)
    resource_id: Mapped[str] = mapped_column(String, index=True)
    principal_id: Mapped[str] = mapped_column(String)
    principal_type: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)

class AppSession(Base):
    __tablename__ = 'app_sessions'
    tenant_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    app_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    active_seconds: Mapped[int] = mapped_column(Integer)
    idle_seconds: Mapped[int] = mapped_column(Integer)
    raw_json: Mapped[str] = mapped_column(Text)

class IngestionBatch(Base):
    __tablename__ = 'ingestion_batches'
    batch_id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String)
    resource: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
