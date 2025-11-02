from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from passlib.context import CryptContext

from services.db import users_col

# Config
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_user(username: str, email: Optional[str], password: str) -> dict:
    # ensure unique username (or email)
    existing = users_col.find_one({"username": username})
    if existing:
        raise ValueError("username already exists")

    hashed = hash_password(password)
    user_doc = {
        "user_id": username,  # simple: use username as user_id; change to UUID if you prefer
        "username": username,
        "email": email,
        "hashed_password": hashed,
        "created_at": datetime.utcnow().isoformat()
    }
    users_col.insert_one(user_doc)
    return user_doc

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = users_col.find_one({"username": username})
    if not user:
        return None
    if not verify_password(password, user.get("hashed_password", "")):
        return None
    return user

def create_access_token(*, data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
