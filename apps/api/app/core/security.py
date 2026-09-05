from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str


def create_token(subject: str, role: str) -> str:
    return jwt.encode({"sub": subject, "role": role}, settings.jwt_secret, algorithm="HS256")


def current_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization:
        # Development mode keeps local synthetic demos usable; production must require JWT.
        if settings.environment == "development":
            return Principal("local-dev", "ADMIN")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return Principal(str(payload["sub"]), str(payload["role"]))
    except (ValueError, KeyError, jwt.PyJWTError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


def require_roles(*roles: str):
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal
    return dependency
