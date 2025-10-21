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
- **TailwindCSS** – Utility-first CSS framework for rapid, maintainable styling.

These choices allow for quick prototyping of the frontend while keeping it modular, responsive, and easy to style.  
The backend uses **Python** with **FastAPI** for a simple, performant API and **MongoDB** for storing user data.

---

## Project Structure

### Backend

```
backend/
├─ main.py            # Sets up FastAPI, CORS middleware, and includes API routes
│
├─ api/
│  ├─ __init__.py     # Marks `api` as a Python package
│  └─ routes.py       # Defines HTTP endpoints (currently /search) and calls the search service
│
├─ services/
│  ├─ __init__.py     # Marks `services` as a Python package
│  ├─ google_api.py   # Encapsulates Google Custom Search API calls
│  └─ search_service.py # Implements the search pipeline, currently proxies to Google API
├─ .env               # Environment variables (Google API key, CX, etc.)
├─ requirements.txt   # Python dependencies
└─ venv/              # Virtual environment (not committed)
```

---

### Frontend

```
frontend/
├─ src/
│  ├─ api/
│  │  └─ search.js              # Handles API calls to backend /search endpoint
│  │
│  ├─ components/
│  │  ├─ SearchBar.jsx          # User input component for entering search queries
│  │  ├─ SearchResults.jsx      # Displays formatted list of search results
│  │  └─ Navbar.jsx             # Navigation bar with links to Search, Profile, and Settings pages
│  │
│  ├─ pages/
│  │  ├─ SearchPage.jsx         # Main search page with query logic and result display
│  │  ├─ UserProfilePage.jsx    # Placeholder for user interests and search history view/edit
│  │  └─ SettingsPage.jsx       # Placeholder for privacy and personalization settings
│  │
│  ├─ App.jsx                   # Defines routes and overall layout (wraps all pages with Navbar)
│  └─ main.jsx                  # React entry point, mounts <App /> into DOM
├─ index.html                   # Root HTML shell for Vite (loads /src/main.jsx)
├─ package.json                 # Project metadata, dependencies, and scripts
├─ vite.config.js               # Vite build and dev server configuration
└─ .env                         # Frontend environment variables (e.g., VITE_API_URL)
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
* `src/index.css` – contains Tailwind imports or current styles.
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
