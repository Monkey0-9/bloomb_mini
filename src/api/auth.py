from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = "sat-trade-proprietary-v1"
ALGORITHM = "HS256"
auth_scheme = HTTPBearer()

# Roles configuration
ROLES = {
    "ADMIN": ["risk", "execution", "research", "market", "signals"],
    "TRADER": ["execution", "market", "signals"],
    "ANALYST": ["market", "signals", "research"],
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
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
