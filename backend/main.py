from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from your frontend (running on Vite at 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Placeholder /search route
@app.get("/search")
async def search(q: str):
    return {
        "results": [
            {"id": 1, "title": f"Mock result for query: {q}"},
            {"id": 2, "title": "Another mock result"},
        ]
    }
