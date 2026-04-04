import os
from datetime import UTC, datetime, timedelta

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

# Institutional Security: Load from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sat-trade-fallback-dev-only-7721")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
auth_scheme = HTTPBearer()

# Roles configuration
ROLES = {
    "ADMIN": ["risk", "execution", "research", "market", "signals"],
    "TRADER": ["execution", "market", "signals"],
    "ANALYST": ["market", "signals", "research"],
}


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(payload: dict = Depends(verify_token)):
    """Dependency to get the current user and their role."""
    return payload

def require_role(allowed_roles: list[str]):
    """Dependency to enforce RBAC."""
    def role_checker(user: dict = Depends(get_current_user)):
        role = user.get("role", "ANALYST")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role {role} not authorized. Required: {allowed_roles}"
            )
        return user
    return role_checker
