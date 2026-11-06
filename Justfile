# ==============================================================================
# Root Justfile - Intelligent Student Support System Workspace
# Directly navigates to subdirectories so commands can run from root
# ==============================================================================

set windows-shell := ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

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

# Convenient aliases for backend server
backend: server
run-backend: server
run-server: server

# Launch Streamlit development & testing UI
streamlit:
    cd Intelligent_Student_Support_Agent; uv run streamlit run scripts/streamlit_app.py

# Run interactive terminal agent CLI
cli:
    cd Intelligent_Student_Support_Agent; uv run python app/main.py --cli

# --- Frontend Application Runtimes ---
# Start React/Vite student portal frontend dev server (port 3000)
frontend:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm.cmd run dev

# Convenient aliases for frontend
client: frontend
run-frontend: frontend
run-client: frontend

# Install frontend npm dependencies
frontend-install:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm.cmd install

# Build frontend production bundle
frontend-build:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm.cmd run build

# Preview built frontend production bundle
frontend-preview:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm.cmd run preview

# Lint frontend codebase
frontend-lint:
    cd Intelligent_Student_Support_Agent/Frontend/student-portal; npm.cmd run lint

# --- One-Click Full Stack Startup (Opens Backend & Frontend in Dedicated Windows) ---
dev:
    cd Intelligent_Student_Support_Agent; docker compose up -d
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd 'Intelligent_Student_Support_Agent'; Write-Host '=== Backend API Server (Port 8000) ===' -ForegroundColor Cyan; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd 'Intelligent_Student_Support_Agent/Frontend/student-portal'; Write-Host '=== Frontend Student Portal (Port 3000) ===' -ForegroundColor Green; npm.cmd run dev"

start: dev
run: dev
app: dev

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
