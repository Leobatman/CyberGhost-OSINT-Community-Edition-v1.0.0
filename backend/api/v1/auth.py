from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Any

from backend.core.database import get_db
from backend.models.models import User, Role, Permission
from backend.core.security.jwt import create_access_token, create_refresh_token

# Nota: Assumimos que existe um core.security.password para verificar senhas
# from backend.core.security.password import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Autentica o usuário e retorna Access e Refresh tokens com contexto Multi-tenant.
    """
    # 1. Fetch user (dummy query para V15 skeleton, ajuste conforme o hash)
    # user = db.scalars(select(User).where(User.username == form_data.username)).first()
    # if not user or not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Mocking successful login para o esqueleto do V15
    tenant_id = "00000000-0000-0000-0000-000000000000" # Dummy
    user_id = "11111111-1111-1111-1111-111111111111"
    role_name = "Admin"
    permissions = ["scan:read", "scan:write", "ioc:delete"]
    
    # 2. Construir Payload
    token_payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role_name,
        "permissions": permissions
    }
    
    # 3. Gerar Tokens
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "tenant_id": tenant_id
    }
