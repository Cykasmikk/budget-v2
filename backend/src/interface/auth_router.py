from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.interface.dependencies import get_db
from src.application.auth_service import AuthService
from pydantic import BaseModel
from src.infrastructure.limiter import limiter
import os

router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/auth/login")
async def login(
    response: Response,
    creds: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    
    # Initialize default admin if needed (dev mode helper)
    await service.ensure_default_setup()
    
    user = await service.authenticate_user(creds.email, creds.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session = await service.create_session(user)
    
    # Secure Cookie
    is_secure = os.getenv("SECURE_COOKIES", "False").lower() == "true"
    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60 # 1 week
    )
    
    return {"message": "Logged in", "user": user.email, "role": user.role}

# Rate limit for guest access - configurable via env var
# Set GUEST_RATE_LIMIT to "0" to disable rate limiting (development only)
# Default: 20/hour (increased from 5/hour for better dev experience)
GUEST_RATE_LIMIT = os.getenv("GUEST_RATE_LIMIT", "20/hour")

# Conditionally apply rate limiting
def apply_rate_limit(func):
    """Apply rate limit only if not disabled"""
    if GUEST_RATE_LIMIT != "0":
        return limiter.limit(GUEST_RATE_LIMIT)(func)
    return func

@router.post("/auth/guest")
@apply_rate_limit
async def guest_login(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    try:
        service = AuthService(db)
        session = await service.create_guest_access()
        
        # Secure Cookie
        is_secure = os.getenv("SECURE_COOKIES", "False").lower() == "true"
        response.set_cookie(
            key="session_id",
            value=session.id,
            httponly=True,
            secure=is_secure, 
            samesite="lax",
            max_age=24 * 60 * 60 # 24 hours for guest
        )
        
        return {"message": "Guest access granted", "details": "Ephemeral tenant created with sample data"}
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.exception("guest_login_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create guest access: {str(e)}")

@router.get("/auth/me")
async def get_current_user(
    response: Response,
    db: AsyncSession = Depends(get_db),
    session_id: str | None = Cookie(default=None)
):
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")
    
    service = AuthService(db)
    user = await service.get_user_by_session(session_id)
    if not user:
        response.delete_cookie("session_id")
        raise HTTPException(status_code=401, detail="Invalid session")
        
    return {"user": user.email, "role": user.role}

@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("session_id")
    return {"message": "Logged out"}

# --- SSO Endpoints ---

class SSOInitRequest(BaseModel):
    callback_url: str # Where frontend wants to return to (usually /auth/callback)
    email: str | None = None # For domain-hinting logic if we had multi-tenant lookup

@router.post("/auth/sso/init")
async def init_sso(
    request: SSOInitRequest,
    db: AsyncSession = Depends(get_db)
):
    # In a real multi-tenant app, we would look up Tenant by Domain from email
    # For now, we assume the "Default Organization" since we only have one persistent tenant
    from sqlalchemy import select
    from src.infrastructure.models import TenantModel
    from src.application.sso_service import SSOService
    
    stmt = select(TenantModel).where(TenantModel.name == "Default Organization")
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
         raise HTTPException(status_code=404, detail="Organization not found")

    sso_service = SSOService()
    try:
        redirect_url = await sso_service.generate_login_url(tenant, request.callback_url)
        return {"redirect_url": redirect_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class SSOCallbackRequest(BaseModel):
    code: str
    callback_url: str

@router.post("/auth/sso/callback")
async def sso_callback(
    payload: SSOCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # 1. Look up Tenant (Default Org)
    from sqlalchemy import select
    from src.infrastructure.models import TenantModel, UserModel
    from src.application.sso_service import SSOService
    from src.domain.user import UserRole
    
    stmt = select(TenantModel).where(TenantModel.name == "Default Organization")
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
         raise HTTPException(status_code=404, detail="Organization not found")

    # 2. Exchange Code
    sso_service = SSOService()
    try:
        token_data = await sso_service.exchange_code(tenant, payload.code, payload.callback_url)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SSO Exchange Failed: {str(e)}")
        
    # 3. Verify ID Token
    id_token = token_data.get("id_token")
    if not id_token:
         raise HTTPException(status_code=400, detail="No ID Token returned")
         
    try:
        claims = await sso_service.verify_id_token(tenant, id_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    email = claims.get("email") or claims.get("preferred_username")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in SSO token")
        
    # 4. Find or Create User
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    service = AuthService(db)
    
    if not user:
        # JIT Provisioning
        user = UserModel(
            tenant_id=tenant.id,
            email=email,
            role=UserRole.VIEWER, # Default role
            hashed_password=None # Managed by SSO
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Re-fetch as domain User
        from src.domain.user import User
        user_domain = User(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            created_at=user.created_at
        )
    else:
        # Get existing user domain object
        from src.domain.user import User
        user_domain = User(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login
        )

    # 5. Create Session
    session = await service.create_session(user_domain)
    
    # Secure Cookie logic
    is_secure = os.getenv("SECURE_COOKIES", "False").lower() == "true"
    if not is_secure:
        # Log warning if in production context (heuristic: missing localhost in url? hard to know)
        # We just log it.
        import structlog
        logger = structlog.get_logger()
        logger.warning("security_risk_insecure_kookie", message="Setting session cookie without Secure flag")

    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        secure=is_secure, 
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return {"message": "Logged in via SSO", "user": user.email}
