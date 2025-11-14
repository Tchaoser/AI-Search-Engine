# AI-Search-Engine

AI-Search-Engine is a capstone project to build an intelligent web search agent that delivers a personalized search experience.  
The system is planned to leverage user interests and search history to:

- Learn and model individual preferences over time.
- Enhance query understanding through semantic analysis.
- Rank and filter search results for higher relevance.
- Maintain secure, efficient, and privacy-conscious client-server communication.

This personalization aims to improve search relevance, reduce time spent finding information, and provide a more satisfying user experience.

---

## Tech Stack Overview

- **React** – Component-based library for building responsive, dynamic web interfaces.
- **Vite** – Lightweight build tool for fast development and hot module reloading.

These choices allow for quick prototyping of the frontend while keeping it modular, responsive, and easy to style.  
The backend uses **Python** with **FastAPI** for a simple, performant API and **MongoDB** for storing user data.

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
│  ├─ db.py                        # MongoDB connection and collection handles
│  ├─ google_api.py                # Google Custom Search API calls
│  ├─ search_service.py            # Search pipeline (proxies to Google and logs queries/interactions)
│  ├─ semantic_expansion.py        # Expands a user query into a richer one using an Ollama model.
│  ├─ user_profile_service.py      # Aggregates queries/clicks and builds per-user interest profiles
│  └─ auth_service.py              # Handles user creation, authentication, and JWT tokens
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

---

# AI Search Engine: Development Setup & Integration Guide

This document describes the required first-time setup and the steps needed during subsequent development sessions. Ollama is included in the initial setup because semantic expansion is part of normal development.

---

## First-Time Setup

These steps must be done once on a given machine.

### Prerequisites

Install:

* Node.js (v18+)
* Python 3.10+
* Git
* An IDE such as IntelliJ or VS Code

### Clone the Repository

```bash
git clone https://github.com/Tchaoser/AI-Search-Engine.git
cd AI-Search-Engine
```

### Frontend Setup

Install dependencies:

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```
VITE_API_URL=http://localhost:5000
```

This file is git-ignored.

### Backend Setup

Create and activate a virtual environment:

```powershell
cd ../backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

(macOS/Linux: `source venv/bin/activate`)

Install backend dependencies:

```bash
pip install -r requirements.txt
```

### Ollama Installation and Model Setup

Install Ollama based on your operating system:

**Windows**
Install the official Ollama for Windows, then run:

```
ollama serve
```

**macOS**

```
brew install --cask ollama
ollama serve
```

**Linux**

```
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

Ollama listens on `http://127.0.0.1:11434` by default.

Pull the model used by the backend:

```
ollama pull llama3.1
```

If GPU memory is limited:

```
ollama pull llama3.2:3b
```

### Backend Environment Configuration

Add the following to `backend/.env`:

```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TEMP=0.4
ENABLE_SEMANTIC_EXPANSION=1
```

`OLLAMA_TEMP` affects determinism:

* 0.0–0.2: deterministic
* 0.3–0.6: balanced (recommended)
* 0.7–1.0: more creative

A value of `0.4` is appropriate for this project.

---

## Daily Development Workflow

These steps must be performed each time you begin a development session.

1. Start Ollama:

   ```
   ollama serve
   ```

2. Activate the backend virtual environment:

   ```
   cd backend
   .\venv\Scripts\Activate.ps1
   ```

   (macOS/Linux: `source venv/bin/activate`)

3. Run the backend:

   ```
   uvicorn main:app --reload --port 5000
   ```

4. Run the frontend:

   ```
   cd ../frontend
   npm run dev
   ```

Open the printed local URL (typically `http://localhost:5173/`) in a browser. Entering a search query should return results, confirming frontend–backend integration.

---

## Testing and Diagnostics

Check that Ollama is responding:

```
curl http://127.0.0.1:11434/api/tags
```

Generate a simple response:

```
curl -s http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.1","prompt":"say hi","stream":false}'
```

Test end-to-end semantic expansion through the backend:

```
curl -s "http://localhost:5000/search?q=solar%20panel%20tax%20incentives"
```

A valid JSON response and backend logs showing both raw and expanded queries confirm the system is working.

---

## Troubleshooting

**Port 11434 already in use**

```
netstat -ano | findstr :11434
taskkill /PID <PID> /F
```

**GPU/VRAM errors**

```
set OLLAMA_NO_GPU=1
ollama serve
```

or pull a smaller model:

```
ollama pull llama3.2:3b
```

**Changing Ollama port**

```
set OLLAMA_HOST=127.0.0.1:11435
ollama serve
```

Update `OLLAMA_URL` in `.env`.

**MongoDB SSL handshake or connection error**
The IP is not whitelisted.
In MongoDB Atlas: Database → Network Access → IP Access List → Add current IP.
