from fastapi import APIRouter, Body, HTTPException
from services import auth_service

router = APIRouter()

@router.post("/auth/register")
async def register(body: dict = Body(...)):
    """
    Expects {"username": "...", "email": "...", "password": "..."}
    """
    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        user = auth_service.create_user(username=username, email=email, password=password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"user_id": user["user_id"], "username": user["username"]}

@router.post("/auth/login")
async def login(form_data: dict = Body(...)):
    """
    Accepts JSON payload: {"username": "...", "password": "..."}
    Returns access token and user_id.
    """
    username = form_data.get("username")
    password = form_data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    user = auth_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth_service.create_access_token(data={"sub": user["user_id"]})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"]}
