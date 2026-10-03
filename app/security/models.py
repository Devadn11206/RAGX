from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    user_id: str
    tenant_id: str
    roles: List[str]
    active: bool = True

class DocumentACL(BaseModel):
    tenant_id: str
    allowed_roles: List[str]
    allowed_users: List[str]
    classification: str

class AuditEvent(BaseModel):
    event_id: str
    request_id: str
    timestamp: datetime
    user_id: str
    tenant_id: str
    action: str
    document_ids: List[str]
    chunk_ids: List[str]
    status: str
    query_hash: Optional[str] = None
