from functools import wraps
from typing import Any, Callable, TypeVar
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from backend.core.database import get_db

T = TypeVar("T", bound=Callable[..., Any])

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request):
        # O middleware injeta request.state.user e request.state.tenant_id
        user = getattr(request.state, "user", None)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
            
        # O papel seria armazenado na claim do JWT ou no request.state.user.role.name
        user_role = getattr(user, "role_name", None)
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role: {user_role}",
            )
        
        return user


def require_permissions(*required_permissions: str) -> Callable[[T], T]:
    """
    Decorator para verificar permissões granulares.
    """
    def decorator(func: T) -> T:
        @wraps(func)
        async def wrapper(*args: Any, request: Request, db: Session = Depends(get_db), **kwargs: Any) -> Any:
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

            # Aqui você faria um JOIN na tabela user -> roles -> role_permissions -> permissions
            # Para evitar hit no banco em cada request, as permissões devem vir no payload do JWT
            user_permissions = getattr(request.state, "permissions", [])
            
            missing = [p for p in required_permissions if p not in user_permissions]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing)}",
                )
                
            return await func(*args, request=request, db=db, **kwargs)
        return wrapper # type: ignore
    return decorator
