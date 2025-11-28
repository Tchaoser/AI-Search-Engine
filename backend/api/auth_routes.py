from fastapi import APIRouter, Body, HTTPException
from services import auth_service
from services.logger import AppLogger

router = APIRouter()
logger = AppLogger.get_logger(__name__)


@router.post("/auth/register")
async def register(body: dict = Body(...)):
    """
    Expects {"username": "...", "email": "...", "password": "..."}
    """
    username = body.get("username")
    email = body.get("email")
    password = body.get("password")
    if not username or not password:
        logger.warning("Registration failed: missing credentials", extra={"username": username})
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        user = auth_service.create_user(username=username, email=email, password=password)
        logger.info("User registered successfully", extra={
            "user_id": user["user_id"],
            "username": username,
            "email": email
        })
    except ValueError as e:
        logger.warning("Registration failed: duplicate or invalid user", extra={
            "username": username,
            "error": str(e)
        })
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
        logger.warning("Login attempt: missing credentials", extra={"username": username})
        raise HTTPException(status_code=400, detail="username and password required")
    user = auth_service.authenticate_user(username, password)
    if not user:
        logger.warning("Login failed: invalid credentials", extra={"username": username})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth_service.create_access_token(data={"sub": user["user_id"]})
    logger.info("User login successful", extra={
        "user_id": user["user_id"],
        "username": username
    })
    return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"]}
