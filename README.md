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
│  ├─ App.jsx                        # Defines routes and overall layout
│  ├─ index.css                      # Global styles                 
│  └─ main.jsx                       # React entry point, mounts <App /> into DOM
├─ index.html                        # Root HTML shell for Vite (loads /src/main.jsx)
├─ package.json                      # Project metadata, dependencies, and scripts
├─ vite.config.js                     # Vite build and dev server configuration
└─ .env                               # Frontend environment variables (e.g., VITE_API_URL)
```

---

This structure:

* Keeps backend modular and extensible: `main.py` is minimal, API routes and services are separated.
* Frontend components and API calls are isolated for easy expansion.
* `.env` usage centralizes sensitive keys and configuration.
* We don’t use a `src/` folder in the backend because keeping `main.py` and packages at the root avoids import issues with FastAPI and Uvicorn, making module paths simpler and easier to run.

## Frontend + Backend Setup (Integration Test)

This guide explains how to set up the frontend and backend environments and run the integration test for AI-Search-Engine, confirming that the frontend can successfully call the backend.

---

### Prerequisites

Make sure the following software is installed:

- **Node.js** (v18+ recommended)  
  [Download Node.js](https://nodejs.org/)

- **npm** (comes with Node.js)

- **Python 3.10+**  
  [Download Python](https://www.python.org/)

- **Git**  
  [Download Git](https://git-scm.com/)

- IDE: IntelliJ or similar.

---

### 1. Clone the Repository

```bash
git clone https://github.com/Tchaoser/AI-Search-Engine.git
cd AI-Search-Engine
```

---

### 2. Frontend Setup

```bash
cd frontend
npm install
```

This installs React, TailwindCSS, Axios, and other required packages.

#### 2a. Configure Environment Variables

Create a `.env` file inside the `frontend` folder:

```
VITE_API_URL=http://localhost:5000
```

> **Note:** This file is already in `.gitignore`. Future backend changes may require updating this URL. Do not commit `.env`.

#### 2b. Verify Frontend Files

Make sure the following key files exist:

* `src/App.jsx` – dummy component fetching `/search` results.
* `src/index.css` – contains current styles.
* `vite.config.js` – default Vite + React configuration.
* `package.json` – contains dependencies and dev scripts.

#### 2c. Run Frontend

```bash
npm run dev
```

* Vite will start a dev server.
* Check the terminal output for the local URL (default: `http://localhost:5173/`).
* Open this URL in your browser.

You should see:

* The "AI Search Dev" heading.
* A search bar

> **Note:** At this stage, the frontend is fully decoupled from the backend. You can safely modify components or styles without breaking future integration.

---

### 3. Backend Setup

#### 3a. Create & Activate Virtual Environment (PowerShell)

```powershell
cd ../backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Linux/macOS alternative:** `source venv/bin/activate`

> **Tip:** Admin privileges and adding Python to PATH can help avoid issues during installation.

#### 3b. Install Backend Dependencies

The repository includes `requirements.txt` with:

```
fastapi
uvicorn
pymongo
python-dotenv
requests
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

#### 3c. Run Backend

```powershell
uvicorn main:app --reload --port 5000
```

Backend will run at `http://localhost:5000`.

##### Check Backend

1. Test the `/search` endpoint:

```powershell
curl "http://localhost:5000/search?q=test"
```

You should see a search bar and subsequent results.

**Note:** If when running your backend you get SSL handshake errors that means you IP address has been rejected by mongoDB. 
            - To fix go into mongoDB and signin, on the databse go to Database & Network option, then the IP access option.
            - Then add your IP to the IP access list, then try redoing your steps above

2. Refresh the frontend page (`http://localhost:5173/`). Mock search results should now appear, confirming the integration works.

---

## 4. Full Integration Test / Quickstart Guide

1. Ensure `.env` in the frontend points to `http://localhost:5000`.
2. Start both servers after cd-ing into each in separate terminals:
    - Frontend: `npm run dev`
    - Backend: `uvicorn main:app --reload --port 5000` (remember to enter the virtual environment first: .\venv\Scripts\Activate.ps1)
3. Open the frontend URL (`http://localhost:5173`) in a browser.  
   If results display after entering a search query, the integration test passes.

This confirms the frontend and backend communicate correctly, and the project is ready for further development.


## 5. Semantic Expansion with Ollama (Local LLM)

This project can enhance queries semantically using a local LLM via **Ollama**. The backend calls Ollama to turn the short user query into a single, more detailed query. This improves recall and relevance without changing the API response shape.


### A) Install and run Ollama

**Windows**
Install the official Ollama for Windows, then in Command Prompt (or PowerShell):
ollama serve

**macOS**
brew install --cask ollama
ollama serve

**Linux**
curl -fsSL https://ollama.com/install.sh | sh
ollama serve

Ollama listens on http://127.0.0.1:11434 by default.

---

### B) Pull a model

Pull the model referenced in the backend:
ollama pull llama3.1 #if you have enough vram, 4gb, use this. The bigger the model the better the results.

Low-VRAM option:
ollama pull llama3.2:3b

---

### C) Backend configuration (.env)

update backend/.env to include this:
```
# --- semantic expansion ---
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_TEMP=0.4

# controlling this feature: 1 = on, 0 = off
ENABLE_SEMANTIC_EXPANSION=1


#### What `OLLAMA_TEMP` Does

`OLLAMA_TEMP` controls the **creativity** or **determinism** of the model’s responses:

| Value   |                   Behavior                         |                     Use Case                         |
|---------|----------------------------------------------------|------------------------------------------------------|
| 0.0–0.2 | Very deterministic (nearly identical outputs).     | When you need consistent query expansion results.    |
| 0.3–0.6 | Balanced (some variability, but still relevant).   | Ideal for semantic query expansion — your case.      |
| 0.7–1.0 | More creative and exploratory responses.           | When you want diverse, alternate phrasings or ideas. |

In this project:
```
OLLAMA_TEMP=0.4
```
means the model will slightly vary its expansions but remain semantically grounded.

### F) Test the LLM path

Smoke test Ollama:
```
curl http://127.0.0.1:11434/api/tags
```

Generate once:
```
curl -s http://127.0.0.1:11434/api/generate -H "Content-Type: application/json" -d '{"model":"llama3.1","prompt":"say hi","stream":false}'
```

End-to-end test:
```
curl -s "http://localhost:5000/search?q=solar%20panel%20tax%20incentives"
```

You should get { "query_id": "...", "results": [...] }. The backend searched with the **enhanced** query and logged both raw_text and enhanced_text in Mongo.

---

### G) Troubleshooting (Windows/NVIDIA)

Port already in use when running ollama serve
Another Ollama instance is likely running. Test:
```
curl http://127.0.0.1:11434/api/tags
```

Or kill the process:
```
netstat -ano | findstr :11434
taskkill /PID <PID> /F
```

CUDA error when starting a large model
Try CPU or a smaller model:
```
set OLLAMA_NO_GPU=1
ollama serve
```

Or:
```
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

Change port
```
set OLLAMA_HOST=127.0.0.1:11435
ollama serve
```

Update OLLAMA_URL in backend/.env accordingly.
