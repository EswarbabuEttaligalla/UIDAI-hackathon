"""
Authentication and Security Module for AMEWS
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.database import get_connection, execute_query_df

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user"""
    query = "SELECT * FROM users WHERE username = ? AND is_active = TRUE"
    df = execute_query_df(query, (username,))
    
    if df.empty:
        return None
    
    user = df.iloc[0]
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    # Update last login
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (datetime.now(), user["user_id"])
        )
    finally:
        conn.close()
    
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "department": user["department"]
    }


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """Get the current authenticated user"""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    subject = payload.get("sub")
    if not subject:
        return None
    
    # Check if this is an OTP-based user (user_id starts with 'usr_')
    if subject.startswith("usr_"):
        # This is an OTP-based test user - return a synthetic user object
        # The actual user data is stored in localStorage on the frontend
        return {
            "user_id": subject,
            "username": subject,
            "full_name": "Test User",
            "role": "ADMIN",  # Grant full access for testing
            "department": "Testing"
        }
    
    # Traditional username-based lookup
    query = "SELECT * FROM users WHERE username = ? AND is_active = TRUE"
    df = execute_query_df(query, (subject,))
    
    if df.empty:
        # If not found in DB, still allow access for demo purposes
        return {
            "user_id": subject,
            "username": subject,
            "full_name": "Demo User",
            "role": "ADMIN",
            "department": "Demo"
        }
    
    user = df.iloc[0]
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "department": user["department"]
    }


async def get_current_user_required(token: str = Depends(oauth2_scheme)) -> dict:
    """Get the current user or raise exception"""
    user = await get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_role(allowed_roles: list):
    """Decorator to require specific roles"""
    async def role_checker(user: dict = Depends(get_current_user_required)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker


def log_audit(action: str, endpoint: str, user_id: str, 
              request_summary: str, response_status: int):
    """Log an audit entry"""
    import uuid
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO audit_logs 
            (log_id, timestamp, action, endpoint, user_id, request_summary, response_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"log_{uuid.uuid4().hex[:12]}",
            datetime.now(),
            action,
            endpoint,
            user_id,
            request_summary,
            response_status,
            datetime.now()
        ))
    finally:
        conn.close()
