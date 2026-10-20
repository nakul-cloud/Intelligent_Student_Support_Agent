# ==============================================================================
# Root Justfile - Delegates to Intelligent_Student_Support_Agent
# ==============================================================================

set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent --list

up:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent up

down:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent down

logs:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent logs

db-init:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent db-init

seed:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent seed

ingest:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent ingest

server:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent server

streamlit:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent streamlit

cli:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent cli

eval:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent eval

audit-chunks:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent audit-chunks

clean:
    just -f Intelligent_Student_Support_Agent/Justfile -d Intelligent_Student_Support_Agent clean
