from datetime import datetime
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.models import AuditLogModel
from src.application.context import get_tenant_id, get_user_id
import structlog

logger = structlog.get_logger()

class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        actor_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None
    ) -> None:
        """
        Records an audit log entry.
        
        Args:
            action: The action performed (e.g., "CREATE", "UPDATE", "DELETE", "LOGIN").
            resource: The resource type affected (e.g., "RULE", "BUDGET_FILE", "SETTINGS").
            resource_id: The identifier of the resource (optional).
            details: Additional context as a dictionary.
            actor_id: The UUID of the user performing the action. Defaults to context user.
            tenant_id: The UUID of the tenant. Defaults to context tenant.
        """
        try:
            effective_tenant = tenant_id or get_tenant_id()
            effective_actor = actor_id or get_user_id()
            
            if not effective_tenant:
                logger.warn("audit_log_skipped_no_tenant", action=action, resource=resource)
                return

            log_entry = AuditLogModel(
                tenant_id=effective_tenant,
                actor_id=effective_actor,
                action=action,
                resource=resource,
                resource_id=resource_id,
                details=details or {},
                timestamp=datetime.utcnow()
            )
            
            self.session.add(log_entry)
            # We flush to ensure it's staged, but commit is usually handled by the caller (Use Case/Router)
            # However, for Audit logs, we often want them to persist even if the main transaction fails (if using a separate session),
            # but here we share the session, so it commits with the transaction.
            # Ideally, audit logs for *failures* should be committed separately.
            # For now, we assume success path logging.
            await self.session.flush()
            
            logger.info("audit_log_created", action=action, resource=resource, tenant_id=str(effective_tenant))
            
        except Exception as e:
            logger.error("audit_log_failed", error=str(e))
            # Do not raise, so we don't break the main business flow
