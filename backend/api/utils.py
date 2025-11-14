from fastapi import Header
from services import auth_service


async def get_user_id_from_auth(authorization: str = Header(None)):
    if not authorization:
        return "guest"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return "guest"
    token = parts[1]
    payload = auth_service.decode_access_token(token)
    return payload.get("sub") or payload.get("user_id") or "guest"
