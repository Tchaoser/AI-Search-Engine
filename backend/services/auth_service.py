from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from services.db import users_col
from services.logger import AppLogger

# Config
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

logger = AppLogger.get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_user(username: str, email: Optional[str], password: str) -> dict:
    # ensure unique username (or email)
    existing = users_col.find_one({"username": username})
    if existing:
        logger.warning("User creation failed: username already exists", extra={"username": username})
        raise ValueError("username already exists")

    try:
        hashed = hash_password(password)
    except Exception as e:
        logger.error("Password hashing failed", extra={"username": username}, exc_info=True)
        raise

    user_doc = {
        "user_id": username,  # simple: use username as user_id; change to UUID if you prefer
        "username": username,
        "email": email,
        "hashed_password": hashed,
        "created_at": datetime.utcnow().isoformat()
    }
    users_col.insert_one(user_doc)
    logger.debug("User document inserted", extra={
        "user_id": user_doc["user_id"],
        "username": username
    })
    return user_doc

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = users_col.find_one({"username": username})
    if not user:
        logger.debug("Authentication failed: user not found", extra={"username": username})
        return None
    if not verify_password(password, user.get("hashed_password", "")):
        logger.debug("Authentication failed: invalid password", extra={"username": username})
        return None
    logger.debug("User authenticated", extra={"username": username})
    return user

def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug("Access token created", extra={"sub": to_encode.get("sub")})
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create access token", extra={"sub": to_encode.get("sub")}, exc_info=True)
        raise

def decode_access_token(token: str) -> Optional[dict]:
    # Let JWT-related errors propagate so callers can distinguish
    # between expired and otherwise invalid tokens.
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
