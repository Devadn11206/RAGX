from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt import decode_access_token
from app.security.models import User
from app.core.exceptions import RAGXException

security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not credentials:
        raise RAGXException(code="UNAUTHORIZED", message="Missing authentication token", status_code=401)
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    roles = payload.get("roles", [])
    
    if not user_id or not tenant_id:
        raise RAGXException(code="INVALID_TOKEN", message="Missing required claims", status_code=401)
        
    return User(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        active=True
    )
