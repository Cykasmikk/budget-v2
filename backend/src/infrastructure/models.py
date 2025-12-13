from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, DateTime, JSON, Enum, Uuid
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import uuid
from src.domain.user import UserRole

class Base(DeclarativeBase):
    pass

class TenantModel(Base):
    __tablename__ = "tenants"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    auth_config = Column(JSON, default=dict)
    settings = Column(JSON, default=lambda: {
        "currency": "USD",
        "forecast_horizon": 6,
        "theme": "dark",
        "budget_threshold": 5000
    })
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True) # Secure token string
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    actor_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)

class BudgetModel(Base):
    __tablename__ = "budget_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String, nullable=False)
    project = Column(String, nullable=True, default="General")

class RuleModel(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    pattern = Column(String, nullable=False)
    category = Column(String, nullable=False)

class GuestUsageStats(Base):
    __tablename__ = "guest_usage_stats"
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_tenant_id = Column(String, nullable=False) # Stored as string to survive tenant deletion
    original_created_at = Column(DateTime, nullable=False)
    archived_at = Column(DateTime, default=datetime.utcnow)
    
    # aggregated stats
    session_duration_seconds = Column(Integer, default=0)
    total_transactions_logged = Column(Integer, default=0)
    total_budget_value = Column(Numeric(12, 2), default=0)
    feature_usage_summary = Column(JSON, default={}) # e.g. {"forecast_viewed": 1, "simulation_run": 2}
