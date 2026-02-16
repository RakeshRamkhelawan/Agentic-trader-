from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request

from backend.core.auth.models import TokenPayload
from backend.core.auth import context

security = HTTPBearer(auto_error=False)


async def get_current_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenPayload:
    if hasattr(request.state, 'token_payload'):
        return request.state.token_payload
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_tenant(token: TokenPayload = Depends(get_current_token)) -> str:
    return token.tenant_id


async def get_current_user_id(token: TokenPayload = Depends(get_current_token)) -> str:
    return token.sub


def require_roles(*required_roles: str):
    async def role_checker(token: TokenPayload = Depends(get_current_token)) -> TokenPayload:
        if not token.has_any_role(list(required_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}"
            )
        return token
    return role_checker


def require_tenant(allowed_tenants: list[str]):
    async def tenant_checker(tenant_id: str = Depends(get_current_tenant)) -> str:
        if tenant_id not in allowed_tenants:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )
        return tenant_id
    return tenant_checker


class TenantContext:
    def __init__(self, tenant_id: str = Depends(get_current_tenant)):
        self.tenant_id = tenant_id
        context.set_current_tenant(tenant_id)
    
    def get_rls_filter(self) -> dict:
        return {"tenant_id": self.tenant_id}
    
    def apply_to_query(self, query):
        return query.filter_by(tenant_id=self.tenant_id)