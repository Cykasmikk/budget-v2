import structlog
from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.context import set_tenant_id, set_user_id
from src.infrastructure.models import SessionModel, TenantModel
from sqlalchemy import select

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that handles structured logging for every HTTP request.
    Manages structlog context variables (path, method, status_code).
    Captures unhandled exceptions and returns generic 500 error envelopes.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Intercepts requests to bind context vars and log outcomes.
        """
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            path=request.url.path,
            method=request.method,
        )
        
        try:
            response = await call_next(request)
            structlog.contextvars.bind_contextvars(status_code=response.status_code)
            if 400 <= response.status_code < 500:
                logger.warn("request_failed")
            elif response.status_code >= 500:
                logger.error("request_failed")
            else:
                logger.info("request_success")
            return response
        except Exception as e:
            logger.exception("request_failed_with_exception", error=str(e))
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error"}
            )

# Dependency to inject DB session into middleware logic manually if needed, 
# although Middleware runs before FastAPI deps.
# We'll implement a simple Session Middleware that checks a cookie.

# Since we don't have easy dependency injection in Middleware, 
# we'll implement the auth logic in a Depends() function for the routes,
# OR we implement it here by creating a session manually.
# For Clean Architecture + FastAPI, using Dependencies is usually preferred over Middleware for Auth.
# However, for Tenant Context, Middleware is better to ensure it's set early.

# We will skip manual Session middleware for now and handle it via `router.py` dependencies
# that set the ContextVar.
# But we DO need context vars set for Repositories.

async def get_session_dependency(request: Request):
    # This is a dummy dependency signature to help thought process.
    pass
