from datetime import datetime, timezone
from typing import Generic, Literal, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar('T')

class Envelope(BaseModel, Generic[T]):
    tenantId: str = Field(min_length=1)
    source: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    value: list[T]

class GraphItem(BaseModel):
    model_config = ConfigDict(extra='allow')

class ApplicationIn(GraphItem):
    id: str
    appId: str
    displayName: str
    accountEnabled: bool | None = None

class SignInStatus(GraphItem):
    errorCode: int

class SignInIn(GraphItem):
    id: str
    appId: str | None = None
    userId: str | None = None
    createdDateTime: datetime
    status: SignInStatus

class AssignmentIn(GraphItem):
    id: str
    resourceId: str
    principalId: str
    principalType: str | None = None

class SessionIn(BaseModel):
    sessionId: str
    appId: str
    userId: str
    startedAt: datetime
    endedAt: datetime
    activeSeconds: int = Field(ge=0)
    idleSeconds: int = Field(ge=0)
    status: Literal['closed']

    @model_validator(mode='after')
    def valid_duration(self):
        if self.startedAt.utcoffset() is None or self.endedAt.utcoffset() is None:
            raise ValueError('Session timestamps must have timezone')
        elapsed = (self.endedAt - self.startedAt).total_seconds()
        if elapsed <= 0 or not elapsed.is_integer():
            raise ValueError('Session duration must be positive whole seconds')
        if self.activeSeconds + self.idleSeconds != int(elapsed):
            raise ValueError('Active and idle seconds must equal elapsed seconds')
        # MVP: one UTC calendar day per session; cross-midnight splitting deferred.
        if self.startedAt.astimezone(timezone.utc).date() != (self.endedAt - __import__('datetime').timedelta(microseconds=1)).astimezone(timezone.utc).date():
            raise ValueError('Sessions spanning UTC dates are not supported in MVP')
        return self
