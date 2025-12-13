import secrets
import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.user import User, UserRole
from src.domain.session import Session
from src.infrastructure.models import UserModel, SessionModel, TenantModel
from src.application.context import set_tenant_id, set_user_id

from src.domain.auth import AuthProvider

class AuthService(AuthProvider):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verifies the session ID (token) and returns session details.
        """
        session_obj = await self.get_session(token)
        if not session_obj:
            return None
        return {
            "sub": str(session_obj.user_id),
            "exp": session_obj.expires_at.timestamp(),
            "tenant_id": str(session_obj.tenant_id)
        }

    async def get_user(self, token: str) -> Optional[str]:
        """
        Returns the user ID from the session token.
        """
        payload = await self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    async def get_password_hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()

        if not user_model or not user_model.hashed_password:
            return None
        
        if await self.verify_password(password, user_model.hashed_password):
            # Update last login
            user_model.last_login = datetime.utcnow()
            await self.session.commit()
            
            return User(
                id=user_model.id,
                tenant_id=user_model.tenant_id,
                email=user_model.email,
                role=user_model.role,
                created_at=user_model.created_at,
                last_login=user_model.last_login
            )
        return None

    async def create_session(self, user: User, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Session:
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7) # 1 week session
        
        session_model = SessionModel(
            id=session_id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.session.add(session_model)
        await self.session.commit()
        
        return Session(
            id=session_id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()
        
        if not session_model:
            return None
            
        if session_model.expires_at < datetime.utcnow():
            # Clean up expired session
            await self.session.delete(session_model)
            await self.session.commit()
            return None
            
        return Session(
            id=session_model.id,
            user_id=session_model.user_id,
            tenant_id=session_model.tenant_id,
            expires_at=session_model.expires_at,
            ip_address=session_model.ip_address,
            user_agent=session_model.user_agent,
            created_at=session_model.created_at
        )

    async def get_user_by_session(self, session_id: str) -> Optional[User]:
        session = await self.get_session(session_id)
        if not session:
            return None
            
        stmt = select(UserModel).where(UserModel.id == session.user_id)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()
        
        if not user_model:
            return None
            
        return User(
            id=user_model.id,
            tenant_id=user_model.tenant_id,
            email=user_model.email,
            role=user_model.role,
            created_at=user_model.created_at,
            last_login=user_model.last_login
        )

    # Temporary: For initializing the default tenant/user
    async def ensure_default_setup(self):
        # 1. Ensure Default Tenant Exists
        stmt = select(TenantModel).where(TenantModel.name == "Default Organization")
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            tenant = TenantModel(
                name="Default Organization",
                domain="local",
                settings={
                    "currency": "USD",
                    "forecast_horizon": 6,
                    "theme": "dark",
                    "budget_threshold": 5000
                }
            )
            self.session.add(tenant)
            await self.session.flush()
        
        # 2. Ensure Admin User Exists
        stmt = select(UserModel).where(UserModel.email == "admin@example.com")
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            hashed = await self.get_password_hash("admin")
            user = UserModel(
                tenant_id=tenant.id,
                email="admin@example.com",
                role=UserRole.ADMIN,
                hashed_password=hashed
            )
            self.session.add(user)
            await self.session.commit()

    async def create_guest_access(self) -> Session:
        # 1. Create Ephemeral Tenant
        tenant_id = uuid.uuid4()
        tenant = TenantModel(
            id=tenant_id,
            name=f"Guest Organization {str(tenant_id)[:8]}",
            domain=f"guest-{str(tenant_id)[:8]}.example.com",
            auth_config={},
            settings={
                "currency": "USD",
                "forecast_horizon": 6,
                "theme": "dark",
                "budget_threshold": 5000
            }
        )
        self.session.add(tenant)
        
        # 2. Create Admin User
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"admin@guest-{str(tenant_id)[:8]}.example.com",
            role=UserRole.VIEWER, # Downgraded from ADMIN per user request
            hashed_password=None # Passwordless access for guest
        )
        self.session.add(user)
        await self.session.flush()
        
        # 3. Seed Sample Data
        from src.infrastructure.models import BudgetModel
        from datetime import date, timedelta
        import random
        
        categories = ["Cloud Infrastructure", "Staffing & Contractors", "Software Licenses", "Marketing", "Office & G&A"]
        projects = ["Cloud Migration 2.0", "Legacy DC Maintenance", "AI/ML Platform Init", "Security Hardening"]
        
        # Generate 6 months of data
        today = date.today()
        entries = []
        
        for i in range(50):
            cat = random.choice(categories)
            # Higher amounts for Cloud/Staffing
            base_amount = 5000 if cat in ["Cloud Infrastructure", "Staffing & Contractors"] else 1000
            amount = base_amount * random.uniform(0.8, 1.5)
            
            entry = BudgetModel(
                tenant_id=tenant_id,
                date=today - timedelta(days=random.randint(0, 180)),
                category=cat,
                amount=amount,
                description=f"Sample {cat} Expense",
                project=random.choice(projects)
            )
            entries.append(entry)
            
        self.session.add_all(entries)
        await self.session.commit()
        
        # 4. Create Session
        domain_user = User(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            created_at=user.created_at
        )
        
        return await self.create_session(domain_user)
