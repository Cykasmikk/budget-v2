from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.interface.dependencies import get_db, get_current_user
from src.infrastructure.models import TenantModel
from src.domain.user import User, UserRole
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from src.interface.envelope import ResponseEnvelope

router = APIRouter(tags=["Settings"])

class SettingsUpdate(BaseModel):
    currency: Optional[str] = None
    forecast_horizon: Optional[int] = None
    theme: Optional[str] = None
    budget_threshold: Optional[int] = None
    merge_strategy: Optional[str] = None # 'latest' | 'blended' | 'combined'

class AuthConfigUpdate(BaseModel):
    enabled: bool
    provider_name: str # e.g. "Google", "Entra ID"
    client_id: str
    client_secret: str
    issuer_url: str # .well-known discovery base

class CombinedSettingsResponse(BaseModel):
    settings: Dict[str, Any]
    auth_config: Dict[str, Any]

class AuthConfigResponse(BaseModel):
    status: str
    config: Dict[str, Any]

@router.get("/settings", response_model=ResponseEnvelope[CombinedSettingsResponse])
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch latest tenant state
    stmt = select(TenantModel).where(TenantModel.id == user.tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    return ResponseEnvelope.success(data=CombinedSettingsResponse(
        settings=tenant.settings,
        auth_config=tenant.auth_config
    ))

@router.patch("/settings", response_model=ResponseEnvelope[Dict[str, Any]])
async def update_settings(
    settings_update: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(TenantModel).where(TenantModel.id == user.tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Update only provided fields
    current_settings = dict(tenant.settings)
    update_data = settings_update.model_dump(exclude_unset=True)
    current_settings.update(update_data)
    
    # Re-assign to trigger SQLAlchemy detection (if using MutableDict, but we use replace)
    tenant.settings = current_settings
    
    await db.commit()
    return ResponseEnvelope.success(data=tenant.settings)

@router.patch("/settings/auth", response_model=ResponseEnvelope[AuthConfigResponse])
async def update_auth_config(
    auth_update: AuthConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admins can configure SSO")
        
    stmt = select(TenantModel).where(TenantModel.id == user.tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Fetch Metadata automatically
    from src.application.sso_service import SSOService
    sso_service = SSOService()
    try:
        discovery_url = f"{auth_update.issuer_url}/.well-known/openid-configuration"
        metadata = await sso_service.get_provider_metadata(discovery_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to discover OIDC metadata: {str(e)}")

    tenant.auth_config = {
        "enabled": auth_update.enabled,
        "provider_name": auth_update.provider_name,
        "client_id": auth_update.client_id,
        "client_secret": auth_update.client_secret,
        "issuer": auth_update.issuer_url,
        "metadata": metadata # Cache the endpoints
    }
    
    await db.commit()
    return ResponseEnvelope.success(data=AuthConfigResponse(
        status="success", 
        config=tenant.auth_config
    ))
