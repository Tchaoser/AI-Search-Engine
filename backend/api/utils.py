from fastapi import Header, HTTPException
from services import auth_service
from jose.exceptions import ExpiredSignatureError
from jose import JWTError


async def get_user_id_from_auth(authorization: str = Header(None)):
    """
    Permissive dependency: returns the `user_id` when a valid bearer token is provided,
    otherwise returns the string "guest". This is suitable for endpoints that allow
    anonymous access and should continue functioning for guests.
    """
    if not authorization:
        return "guest"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return "guest"
    token = parts[1]
    try:
        payload = auth_service.decode_access_token(token)
    except ExpiredSignatureError:
        # Expired token — treat as guest for permissive endpoints so UI can show limited view
        return "guest"
    except JWTError:
        # Malformed/invalid token — treat as guest
        return "guest"

    return payload.get("sub") or payload.get("user_id") or "guest"


async def require_user_id_from_auth(authorization: str = Header(None)):
    """
    Strict dependency: requires a valid bearer token and returns the `user_id`.
    Raises `HTTPException(status_code=401)` when the token is missing, expired, or invalid.
    Use this for endpoints that must be accessed only by authenticated users.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = parts[1]
    try:
        payload = auth_service.decode_access_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_id
