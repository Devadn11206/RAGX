from fastapi import APIRouter, UploadFile, File, Depends, Form
from app.schemas.documents import DocumentUploadResponse, DocumentMetadata, DocumentPermissionsUpdate
from app.services.document_service import document_service
from app.audit.audit_service import audit_service
from app.security.auth import get_current_user
from app.security.models import User
from typing import List

router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    classification: str = Form("internal"),
    allowed_roles: str = Form(""),
    allowed_users: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    roles = [r.strip() for r in allowed_roles.split(",")] if allowed_roles else []
    users = [u.strip() for u in allowed_users.split(",")] if allowed_users else []
    
    content = await file.read()
    res = await document_service.upload_document(
        filename=file.filename, 
        content=content,
        tenant_id=current_user.tenant_id,
        classification=classification,
        allowed_roles=roles,
        allowed_users=users
    )
    
    await audit_service.log_event(
        request_id="REQ",
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        action="document_ingest",
        status="success",
        document_ids=[res["document_id"]]
    )
    
    return res

@router.get("", response_model=List[DocumentMetadata])
async def list_documents(current_user: User = Depends(get_current_user)):
    docs = await document_service.get_documents()
    # Filter by tenant
    return [d for d in docs if d.get("tenant_id") == current_user.tenant_id]

@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    doc = await document_service.get_document(document_id)
    if doc.get("tenant_id") != current_user.tenant_id:
        from app.core.exceptions import RAGXException
        await audit_service.log_event("REQ", current_user.user_id, current_user.tenant_id, "document_access", "unauthorized", [document_id])
        raise RAGXException(code="FORBIDDEN", message="Unauthorized", status_code=403)
        
    await audit_service.log_event("REQ", current_user.user_id, current_user.tenant_id, "document_access", "success", [document_id])
    return doc

@router.delete("/{document_id}")
async def delete_document(document_id: str, current_user: User = Depends(get_current_user)):
    doc = await document_service.get_document(document_id)
    if doc.get("tenant_id") != current_user.tenant_id:
        from app.core.exceptions import RAGXException
        await audit_service.log_event("REQ", current_user.user_id, current_user.tenant_id, "document_delete", "unauthorized", [document_id])
        raise RAGXException(code="FORBIDDEN", message="Unauthorized", status_code=403)
        
    res = await document_service.delete_document(document_id)
    await audit_service.log_event("REQ", current_user.user_id, current_user.tenant_id, "document_delete", "success", [document_id])
    return res

@router.patch("/{document_id}/permissions")
async def update_permissions(
    document_id: str,
    update_data: DocumentPermissionsUpdate,
    current_user: User = Depends(get_current_user)
):
    doc = await document_service.get_document(document_id)
    if doc.get("tenant_id") != current_user.tenant_id:
        from app.core.exceptions import RAGXException
        await audit_service.log_event("REQ", current_user.user_id, current_user.tenant_id, "permission_change", "unauthorized", [document_id])
        raise RAGXException(code="FORBIDDEN", message="Unauthorized", status_code=403)
        
    classification = update_data.classification if update_data.classification is not None else doc.get("classification")
    allowed_roles = update_data.allowed_roles if update_data.allowed_roles is not None else doc.get("allowed_roles", [])
    allowed_users = update_data.allowed_users if update_data.allowed_users is not None else doc.get("allowed_users", [])
    
    res = await document_service.update_permissions(
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        classification=classification,
        allowed_roles=allowed_roles,
        allowed_users=allowed_users
    )
    
    await audit_service.log_event("REQ", current_user.user_id, current_user.tenant_id, "permission_change", "success", [document_id])
    return res
