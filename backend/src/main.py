
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.interface.envelope import ResponseEnvelope
from contextlib import asynccontextmanager
from src.interface.router import router as api_router
from src.interface.export_router import router as export_router
from src.interface.query_router import router as query_router
from src.interface.rule_router import router as rule_router
from src.interface.simulation_router import router as simulation_router
from src.interface.middleware import LoggingMiddleware


from src.interface.auth_router import router as auth_router
from src.interface.dependencies import RequireAuth
from fastapi import Depends

# Configure Structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

import asyncio
from src.infrastructure.db import AsyncSessionLocal
from src.application.cleanup_service import CleanupService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background Task for Cleanup
    logger = structlog.get_logger()
    
    async def run_cleanup_loop():
        while True:
            try:
                # logger.info("running_background_cleanup")
                async with AsyncSessionLocal() as session:
                    service = CleanupService(session)
                    count = await service.cleanup_expired_guests()
                    if count > 0:
                        logger.info("background_cleanup_completed", deleted_tenants=count)
            except Exception as e:
                logger.error("background_cleanup_error", error=str(e))
                
            # Run every hour
            await asyncio.sleep(3600)

    # Start loop
    cleanup_task = asyncio.create_task(run_cleanup_loop())
    
    yield
    
    # Cancel loop on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.limiter import limiter

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = structlog.get_logger()
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content=ResponseEnvelope.error("Internal Server Error").model_dump()
    )

app.add_middleware(LoggingMiddleware)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1") # Public

from src.interface.settings_router import router as settings_router
from src.interface.ai_chat_router import router as ai_chat_router

# Protected Routes
app.include_router(api_router, prefix="/api/v1", dependencies=[RequireAuth])
app.include_router(export_router, prefix="/api/v1", dependencies=[RequireAuth])
app.include_router(query_router, prefix="/api/v1", dependencies=[RequireAuth])
app.include_router(rule_router, prefix="/api/v1", dependencies=[RequireAuth])
app.include_router(simulation_router, prefix="/api/v1", dependencies=[RequireAuth])
app.include_router(settings_router, prefix="/api/v1", dependencies=[RequireAuth])
app.include_router(ai_chat_router, prefix="/api/v1", dependencies=[RequireAuth])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
