from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.security.jwt import decode_jwt

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Tenta extrair o token do header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = decode_jwt(token)
                request.state.tenant_id = payload.get("tenant_id")
                request.state.user_id = payload.get("sub")
                request.state.permissions = payload.get("permissions", [])
                request.state.role_name = payload.get("role")
            except Exception:
                request.state.tenant_id = None
        else:
            request.state.tenant_id = None
            
        response = await call_next(request)
        return response
