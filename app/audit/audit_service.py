import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from app.infrastructure.postgres import postgres_client

logger = logging.getLogger(__name__)

class AuditService:
    async def log_event(
        self,
        request_id: str,
        user_id: str,
        tenant_id: str,
        action: str,
        status: str,
        document_ids: List[str] = None,
        chunk_ids: List[str] = None,
        query_hash: Optional[str] = None
    ):
        pool = postgres_client.pool
        if not pool:
            logger.error("Audit log failed: PostgreSQL pool not available")
            return
            
        event_id = f"evt_{uuid.uuid4().hex}"
        timestamp = datetime.now(timezone.utc)
        
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO audit_events (
                        event_id, request_id, timestamp, user_id, tenant_id,
                        action, document_ids, chunk_ids, status, query_hash
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                event_id, request_id, timestamp, user_id, tenant_id,
                action, document_ids or [], chunk_ids or [], status, query_hash)
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")

audit_service = AuditService()
