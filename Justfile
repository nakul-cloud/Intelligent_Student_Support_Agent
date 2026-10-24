# ==============================================================================
# Root Justfile - Intelligent Student Support System Workspace
# Directly navigates to subdirectories so commands can run from root
# ==============================================================================

set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

# --- Infrastructure (Docker) ---
# Start Qdrant, Redis, and PostgreSQL containers in background
up:
    cd Intelligent_Student_Support_Agent; docker compose up -d

# Stop and remove running containers
down:
    cd Intelligent_Student_Support_Agent; docker compose down

# Follow container logs
logs:
    cd Intelligent_Student_Support_Agent; docker compose logs -f

# --- Database & Ingestion Setup ---
# Initialize PostgreSQL tables
db-init:
    cd Intelligent_Student_Support_Agent; uv run python scripts/init_db.py

# Seed mock students, fees, and scholarships into PostgreSQL
seed:
    cd Intelligent_Student_Support_Agent; uv run python scripts/seed_db.py

# Parse, chunk, embed, and store student handbook in Qdrant & track in PostgreSQL
ingest:
    cd Intelligent_Student_Support_Agent; uv run python scripts/ingest_handbook.py

# --- Backend Application Runtimes ---
# Start FastAPI backend server with hot-reload (port 8000)
server:
    cd Intelligent_Student_Support_Agent; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Convenient alias for backend server
backend: server

# Launch Streamlit development & testing UI
streamlit:
    cd Intelligent_Student_Support_Agent; uv run streamlit run scripts/streamlit_app.py

# Run interactive terminal agent CLI
cli:
    cd Intelligent_Student_Support_Agent; uv run python app/main.py --cli

# --- Frontend Application Runtimes ---
# Start React/Vite student portal frontend dev server (port 3000)
frontend:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm run dev

# Convenient alias for frontend
client: frontend

# Install frontend npm dependencies
frontend-install:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm install

# Build frontend production bundle
frontend-build:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm run build

# Preview built frontend production bundle
frontend-preview:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm run preview

# Lint frontend codebase
frontend-lint:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm run lint

# --- Benchmarks & Evaluation ---
# Run 8 benchmark evaluation scenarios and output metrics table
eval:
    cd Intelligent_Student_Support_Agent; uv run python scripts/evaluate.py

# Audit chunk fidelity across 5 dimensions (Coverage, Metadata, Boundaries, Integrity, Tables)
audit-chunks:
    cd Intelligent_Student_Support_Agent; uv run python evaluation/evaluate_chunking.py

# Clean temporary log files, traces, and caches
clean:
    cd Intelligent_Student_Support_Agent; powershell -Command "Get-ChildItem -Path logs/*.log, traces/*.json -ErrorAction SilentlyContinue | Remove-Item -Force"
