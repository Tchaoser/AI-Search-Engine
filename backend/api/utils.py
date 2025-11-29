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
    if not payload:
        # TODO: handle expired/invalid token properly:
        #   - Option 1: forcefully log the user out
        #   - Option 2: return an error explaining the token is expired
        return "guest"
    return payload.get("sub") or payload.get("user_id") or "guest"
