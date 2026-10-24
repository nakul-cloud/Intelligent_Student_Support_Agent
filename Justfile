# ==============================================================================
# Root Justfile - Delegates to Intelligent_Student_Support_Agent
# ==============================================================================

set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent --list

# --- Infrastructure (Docker) ---
up:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent up

down:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent down

logs:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent logs

# --- Database & Ingestion Setup ---
db-init:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent db-init

seed:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent seed

ingest:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent ingest

# --- Backend Application Runtimes ---
server:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent server

backend:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent backend

streamlit:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent streamlit

cli:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent cli

# --- Frontend Application Runtimes ---
frontend:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent frontend

client:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent client

frontend-install:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent frontend-install

frontend-build:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent frontend-build

frontend-preview:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent frontend-preview

frontend-lint:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent frontend-lint

# --- Benchmarks & Evaluation ---
eval:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent eval

audit-chunks:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent audit-chunks

clean:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent clean
