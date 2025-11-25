from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth_routes import router as auth_router
from api.search_routes import router as search_router
from api.profile_routes import router as profile_router
from services.background_tasks import start_background_tasks, stop_background_tasks

app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # or ["*"] for dev/testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(profile_router)


# Background tasks lifecycle
@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup."""
    start_background_tasks()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on server shutdown."""
    stop_background_tasks()


# Simple health check endpoint, can be removed
@app.get("/health")
async def health_check():
    return {"status": "ok"}
