"""
Authentication API - Registration, Login, and Token Management.

Endpoints:
- POST /register - Register new user
- POST /login - Login with email/password
- POST /token - Legacy token endpoint (tenant_id/account_id)
- GET /me - Get current user info
"""
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import uuid
import re
from backend.models.user_settings import User, UserProfile, UserPreferences

# JWT
from jose import jwt

# Password hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    pwd_context = None


# Database
from backend.api.deps import get_admin_db

# Try to import settings
try:
    from backend.core.config.settings import settings
    SECRET_KEY = getattr(settings, "SECRET_KEY", "dev-secret-key")
except ImportError:
    SECRET_KEY = "dev-secret-key"

router = APIRouter()


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    if PASSLIB_AVAILABLE:
        try:
            return pwd_context.hash(password)
        except Exception:
            # Fallback if passlib/bcrypt fails (common on Windows without binary)
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest()
    else:
        # Fallback for testing (NOT secure for production!)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    if PASSLIB_AVAILABLE:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Fallback check
            import hashlib
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    else:
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def create_jwt_token(user: User) -> str:
    """Create JWT token for user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "roles": [user.role] if user.role else ["user"],
        "exp": now + timedelta(hours=24),
        "iat": now,
        "iss": "agentic-trader",
        "aud": "agentic-trader-api"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    email: str
    tenant_id: str
    role: str
    full_name: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Legacy schemas
class TokenRequest(BaseModel):
    tenant_id: str
    account_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================================
# REGISTRATION ENDPOINT
# ============================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_admin_db)
):
    """
    Register a new user.
    """
    # Check if email already exists
    existing = await db.execute(
        select(User).where(User.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate unique tenant_id
    tenant_id = f"tenant-{uuid.uuid4().hex[:12]}"
    user_id = str(uuid.uuid4())
    
    # Create user
    user = User(
        id=user_id,
        email=request.email,
        password_hash=hash_password(request.password),
        tenant_id=tenant_id,
        role="user",
        is_active=True,
        is_verified=False
    )
    db.add(user)
    
    # Create profile
    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        full_name=request.full_name
    )
    db.add(profile)
    
    # Create preferences with defaults
    preferences = UserPreferences(
        id=str(uuid.uuid4()),
        user_id=user_id
    )
    db.add(preferences)
    
    await db.commit()
    await db.refresh(user)
    
    # Generate token
    token = create_jwt_token(user)
    
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
            full_name=request.full_name
        )
    )


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_admin_db)
):
    """
    Login with email and password.
    
    Returns JWT token on success.
    """
    # Find user by email with profile
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.email == request.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Get profile for full_name
    full_name = user.profile.full_name if user.profile else None
    
    # Generate token
    token = create_jwt_token(user)
    
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
            full_name=full_name
        )
    )


# ============================================================================
# ME ENDPOINT
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_me(
    request: Request,
    db: AsyncSession = Depends(get_admin_db)
):
    """Get current authenticated user info."""
    # Check if middleware set user info
    if hasattr(request.state, "token_payload") and request.state.token_payload:
        payload = request.state.token_payload
        return UserResponse(
            id=payload.sub,
            email=payload.email or "",
            tenant_id=payload.tenant_id,
            role=payload.roles[0] if payload.roles else "user",
            full_name=None
        )
    
    # Try to get from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False})
        user_id = payload.get("sub")
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
            full_name=user.profile.full_name if user.profile else None
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# LEGACY TOKEN ENDPOINT (for backward compatibility)
# ============================================================================

@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """
    Legacy token endpoint using tenant_id/account_id.
    Kept for backward compatibility.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": request.account_id,
        "tenant_id": request.tenant_id,
        "account_id": request.account_id,
        "roles": ["trader"],
        "exp": now + timedelta(hours=24),
        "iat": now,
        "iss": "agentic-trader",
        "aud": "agentic-trader-api"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}
