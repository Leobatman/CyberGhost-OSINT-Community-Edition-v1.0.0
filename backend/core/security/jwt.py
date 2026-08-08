from datetime import datetime, timedelta, UTC
import jwt
from backend.core.config import settings

# This would ideally be fetched from Vault in production
SECRET_KEY = settings.SECRET_KEY.get_secret_value() if hasattr(settings, "SECRET_KEY") else "dev_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token with Tenant and RBAC context."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    # data should contain: {"sub": str(user.id), "tenant_id": str(tenant.id), "role": "admin", "permissions": ["scan:write"]}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str) -> dict:
    """Decode and verify the JWT."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
