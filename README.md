# AI Search Engine

AI-Search-Engine is a capstone project exploring personalized web search through lightweight AI enhancement. The system models user interests from search behavior and interactions to:

* Adapt results over time based on evolving preferences
* Clarify and enrich queries using semantic analysis
* Re-rank results for improved relevance
* Maintain secure, privacy-conscious client–server communication

The goal is to improve search quality while keeping personalization visible and user-controlled.

---

# Tech Stack

Frontend

* React — component-based UI
* Vite — fast dev server and build tool

Backend

* FastAPI — API and orchestration
* Uvicorn — ASGI server
* Python 3.10+

AI / Search

* Ollama — local LLM inference
* Google Custom Search API — web search results

Database

* MongoDB Atlas — user profiles, queries, interaction logs

---

## Project Structure

### Backend

```
backend/
├─ main.py                         # Sets up FastAPI, CORS middleware, and includes API routers
│
├─ api/
│  ├─ __init__.py                  # Marks `api` as a Python package
│  ├─ auth_routes.py               # Handles /auth/register and /auth/login endpoints
│  ├─ search_routes.py             # Handles /search endpoint and click logging
│  ├─ profile_routes.py            # Handles /profiles endpoints (explicit/implicit interests)
│  └─ utils.py                     # Helper functions, e.g., get_user_id_from_auth
│
├─ models/
│  ├─ __init__.py                  # Marks `models` as a Python package
│  └─ data_models.py               # MongoDB document schemas (queries, interactions, user_profiles)
│
├─ services/
│  ├─ __init__.py                  # Marks `services` as a Python package
│  ├─ auth_service.py              # Handles user creation, authentication, and JWT tokens
│  ├─ db.py                        # MongoDB connection and collection handles
│  ├─ google_api.py                # Google Custom Search API calls
│  ├─ logger.py                    # Centralized logging system (file + console, structured logs)
│  ├─ logging_service.py           # Persists queries, clicks, and feedback events to MongoDB
│  ├─ query_cache.py               # In-memory TTL cache for semantic query expansions
│  ├─ search_service.py            # Search pipeline (Google proxy, logging, expansion, caching)
│  ├─ semantic_expansion.py        # Expands a user query using an LLM, with optional interest-based personalization
│  ├─ interest_selection.py        # Interest selection algorithms (top-K, hybrid) with env-based switching
│  └─ user_profile_service.py      # Aggregates queries/clicks and builds per-user interest profiles

├─ background_tasks/
│  ├─ __init__.py                  # Marks `background_tasks` as a Python package
│  └─ profile_rebuild.py           # Periodic background thread that rebuilds user profiles on a schedule
│
├─ logs/
│  └─ app.log                      # Application runtime logs (structured output from AppLogger)
│
├─ scripts/
│  ├─ __init__.py                  # Marks `scripts` as a Python package
│  └─ build_user_profiles.py       # Standalone script to rebuild profiles for all users from stored data
│
├─ .env                            # Environment variables (Google API key, CX, Mongo URI, SECRET_KEY, etc.)
├─ requirements.txt                # Python dependencies
└─ venv/                           # Virtual environment
```

---

### Frontend

```
frontend/
├─ src/
│  ├─ api/
│  │  └─ search.js                  # Handles API calls to backend /search endpoint
│  │
│  ├─ auth/
│  │  └─ auth.js                    # Helper functions for login, logout, current user, and auth headers
│  │
│  ├─ components/
│  │  ├─ SearchBar.jsx              # User input component for entering search queries
│  │  ├─ SearchResults.jsx          # Displays formatted list of search results
│  │  └─ Navbar.jsx                 # Navigation bar with links to Search, Profile, and Settings pages
│  │  └─ Footer.jsx                 # Space for project metadata
│  │
│  ├─ notifications/
│  │  ├─ NotificationProvider.jsx   # React Context provider & hook for notifications
│  │  └─ notifications.css          # Styles for notifications
│  │
│  ├─ pages/
│  │  ├─ SearchPage.jsx             # Main search page with query logic and result display
│  │  ├─ UserProfilePage.jsx        # Page for user interests and search history view/edit
│  │  ├─ SettingsPage.jsx           # Placeholder page for privacy and personalization settings
│  │  ├─ LoginPage.jsx              # Login form with username/password and redirects after login
│  │  └─ RegisterPage.jsx           # Registration form for new users
│  │
│  ├─ App.jsx                       # Defines routes and overall layout
│  ├─ index.css                     # Global styles                 
│  └─ main.jsx                      # React entry point, mounts <App /> into DOM
├─ index.html                       # Root HTML shell for Vite (loads /src/main.jsx)
├─ package.json                     # Project metadata, dependencies, and scripts
├─ vite.config.js                   # Vite build and dev server configuration
└─ .env                             # Frontend environment variables (e.g., VITE_API_URL)
```

# Environment Variables

The project requires `.env` files for both backend and frontend.

These files are **not committed** to the project repository for security reasons.

Create them using the templates below. 

Please Contact the developers (e.g., Peter Grose (PETERGROSE@cmail.carleton.ca) for assistance in connecting to the 
    database, google API, LLM, or other external services if a new connection is not desired)

---

# Backend Environment Variables

Create:

```
backend/.env
```

## Required Configuration

```
# Google Custom Search
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX=your_custom_search_engine_id

# MongoDB
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB_NAME=ai_search_dev

# Authentication
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Ollama / LLM

```
OLLAMA_URL=http://localhost:11434/
OLLAMA_MODEL=llama3.1
OLLAMA_TEMP=0.4
```

## Optional Cache Configuration

```
QUERY_CACHE_TTL=3600
```

Set to 0 to disable caching.

## Optional Interest Selection Configuration

```
SE_INTEREST_SELECTION_ALGO=top_k
SE_EXP_TOP_K_EXPLICIT=5
SE_EXP_TOP_K_IMPLICIT=5

SE_HYBRID_CORE_N=2
SE_HYBRID_POOL_SIZE=10
SE_HYBRID_DETERMINISTIC=1
```

## Optional Security / Proxy

```
ENABLE_PINNING=False
SECURE_PROXY_URL=http://localhost:8000
```

---

# Frontend Environment Variables

Create:

```
frontend/.env
```

```
VITE_API_URL=http://localhost:5000
ENABLE_PINNING=False
SECURE_PROXY_URL=http://localhost:8000
```

---

# First-Time Setup

## Prerequisites

Install:

* Node.js (v18+)
* Python 3.10+
* Git
* Docker Desktop
* Ollama

---

# Clone Repository

```
git clone https://github.com/Tchaoser/AI-Search-Engine.git
cd AI-Search-Engine
```

---

# Backend Setup

Create virtual environment:

Windows:

```
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```
cd backend
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# Frontend Setup

```
cd frontend
npm install
```

---

# Ollama Setup

Install Ollama and start:

```
ollama serve
```

Pull model:

```
ollama pull llama3.1
```

Lower VRAM alternative:

```
ollama pull llama3.2:3b
```

---

# Docker Setup (Optional)

Start Ollama container:

```
docker compose up -d ollama
```

Pull model inside container:

```
docker exec -it ollama ollama pull llama3.1
```

Run full stack:

```
docker compose up --build
```

Detached:

```
docker compose up -d --build
```

---

# Running the Application

Start backend:

```
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 5000
```

Start frontend:

```
cd frontend
npm run dev
```

Open:

```
http://localhost:5173
```

---

# Daily Development Workflow

1. Start Ollama

```
ollama serve
```

2. Start backend

```
cd backend
uvicorn main:app --reload --port 5000
```

3. Start frontend

```
cd frontend
npm run dev
```

---

# Testing

Check Ollama:

```
curl http://127.0.0.1:11434/api/tags
```

Test generation:

```
curl -s http://127.0.0.1:11434/api/generate \
-H "Content-Type: application/json" \
-d '{"model":"llama3.1","prompt":"say hi","stream":false}'
```

Test search endpoint:

```
curl "http://localhost:5000/search?q=test"
```

---

# Personalization Model

The system models two types of interests:

Explicit interests

* user-defined
* normalized weights 0..1

Implicit interests

* inferred from behavior
* numeric scoring

These are never merged and are provided separately to the LLM.

---

# Interest Selection Algorithms

Top-K (default)

* deterministic
* most stable

Hybrid

* deterministic core
* sampled tail
* optional deterministic sampling

Configured via environment variables.

---

# Troubleshooting

Port already in use:

```
netstat -ano | findstr :11434
```

Kill process:

```
taskkill /PID <PID> /F
```

Disable GPU:

```
set OLLAMA_NO_GPU=1
ollama serve
```

MongoDB connection issues:

Whitelist IP in MongoDB Atlas Network Access.

---

# Security Notes

* `.env` files are ignored by git
* do not commit API keys
* rotate keys before submission
* use `.env.example` templates for distribution

---

# License

SYSC 4907 Group 9 Capstone engineering project. For educational use only.
