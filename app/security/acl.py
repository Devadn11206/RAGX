from qdrant_client.http import models
from app.security.models import User
import logging

logger = logging.getLogger(__name__)

def build_acl_filter(user: User) -> models.Filter:
    """Builds a Qdrant filter to enforce ACLs during vector search."""
    
    # Base condition: Tenant must match
    must_conditions = [
        models.FieldCondition(
            key="tenant_id",
            match=models.MatchValue(value=user.tenant_id)
        )
    ]
    
    # Should conditions: Role matches OR User explicitly allowed OR Document has no restrictions (public within tenant)
    # If a document specifies allowed_roles or allowed_users, it's restricted.
    should_conditions = [
        # Explicit user match
        models.FieldCondition(
            key="allowed_users",
            match=models.MatchAny(any=[user.user_id])
        )
    ]
    
    # Role match
    if user.roles:
        should_conditions.append(
            models.FieldCondition(
                key="allowed_roles",
                match=models.MatchAny(any=user.roles)
            )
        )
        
    # Unrestricted (public) condition within the tenant
    should_conditions.append(
        models.IsEmptyCondition(
            is_empty=models.PayloadField(key="allowed_roles")
        )
    )
        
    return models.Filter(
        must=[
            *must_conditions,
            models.Filter(should=should_conditions)
        ]
    )

def verify_chunk_acl(user: User, payload: dict) -> bool:
    """Defense-in-depth check after retrieval."""
    chunk_tenant = payload.get("tenant_id")
    if chunk_tenant != user.tenant_id:
        logger.error(f"SECURITY VIOLATION: Cross-tenant leakage detected! User {user.tenant_id} retrieved chunk from {chunk_tenant}")
        return False
        
    allowed_roles = payload.get("allowed_roles") or []
    allowed_users = payload.get("allowed_users") or []
    
    # If no restrictions, allow (within tenant)
    if not allowed_roles and not allowed_users:
        return True
        
    # Check user explicitly
    if user.user_id in allowed_users:
        return True
        
    # Check roles
    for role in user.roles:
        if role in allowed_roles:
            return True
            
    logger.error(f"SECURITY VIOLATION: RBAC failure detected! User {user.user_id} missing roles for chunk.")
    return False
