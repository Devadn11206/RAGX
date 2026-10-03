from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    status: str

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_hash: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    status: str
    tenant_id: Optional[str] = None
    classification: Optional[str] = None
    allowed_roles: Optional[list] = None
    allowed_users: Optional[list] = None

class DocumentPermissionsUpdate(BaseModel):
    classification: Optional[str] = None
    allowed_roles: Optional[list[str]] = None
    allowed_users: Optional[list[str]] = None
