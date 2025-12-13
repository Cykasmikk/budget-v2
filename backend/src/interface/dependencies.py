from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.db import get_session
from src.application.auth_service import AuthService
from src.application.context import set_tenant_id, set_user_id
from src.domain.user import User

# Standard naming convention alias
get_db = get_session

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    service = AuthService(db)
    service = AuthService(db)
    user = await service.get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    # Set Context for Repositories
    set_tenant_id(user.tenant_id)
    set_user_id(user.id)
    
    return user

# Alias for route protection
RequireAuth = Depends(get_current_user)
