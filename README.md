# Intelligent Student Support Agent

> **End-Term Capstone Project: Agentic AI Engineering**  
> An enterprise-grade, multi-turn conversational AI student support system built with clean modular architecture, dual-tier stateful memory, structure-aware RAG, PostgreSQL database tracking, and turn-by-turn observability.

---

## 🏛️ System Architecture

```
                    ┌─────────────────────────┐
                    │      FastAPI / UI       │
                    │   (Streamlit / CLI)     │
                    └────────────┬────────────┘
                                 │ HTTP / Session
                    ┌────────────▼────────────┐
                    │    Agent Controller     │
                    └────────────┬────────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     │                           │                           │
┌────▼─────────────────┐  ┌──────▼─────────────┐   ┌─────────▼───────────────┐
│     Agent Loop       │  │ Dual-Tier Memory   │   │  Ingestion & Retrieval  │
│  (Groq Llama 3.3 /   │  │ • Redis (Short)    │   │ • Structure-Aware Chunk │
│   OpenAI Tool-Calls) │  │ • Postgres (Long)  │   │ • Qdrant Vector Store   │
└────────────┬─────────┘  └────────────────────┘   └─────────────────────────┘
             │
   ┌─────────┴─────────┐
   │ Real-World Tools  │
   │ • Fee Records     │
   │ • Scholarship DB  │
   │ • Ticket Registry │
   │ • Handbook RAG    │
   └───────────────────┘
```

---

## 🚀 Key Highlights & Deliverables

1. **Section-Aware Policy RAG**:
   - Parses the 44-page official student handbook preserving chapter headings, numbered rules (e.g. Section 10.2 attendance eligibility), and grading tables.
   - Embeds locally via `Orange/orange-nomic-v1.5-1536` with Qdrant vector storage.
2. **Chunking Fidelity & Ingestion Evaluation**:
   - Automated 5-dimension auditor testing Text Coverage, Metadata Provenance, Boundary Quality, Text Integrity, and Table Integrity.
   - **100% Text Coverage, 100% Metadata Accuracy, 100% Text Integrity, 100% Table Integrity**.
   - 📄 [View Chunking Audit Report](Intelligent_Student_Support_Agent/evaluation/results/README.md)
3. **Dual-Tier Stateful Memory**:
   - Fast Redis sliding-window cache for active conversation session context.
   - Durable PostgreSQL storage for cross-session student preferences and profile facts with sensitive topic filtering.
4. **Turn-by-Turn Local Tracer**:
   - Logs tool latency, prompt tokens, completion tokens, and reasoning trajectories to `traces/*.json`.

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11 or 3.12 (`uv` package manager recommended)
- Just command runner (`just`)

### 2. Launch Local Infrastructure
```bash
# Start PostgreSQL, Redis, and Qdrant containers
just up

# Initialize database schema (8 tables) and seed mock records
just db-init
just seed

# Ingest and embed the 44-page student handbook into Qdrant
just ingest
```

### 3. Run Chunking Fidelity Audit
```bash
just audit-chunks
# Generates executive report at Intelligent_Student_Support_Agent/evaluation/results/README.md
```

### 4. Start the Application
```bash
# FastAPI Backend Server (http://localhost:8000)
just server

# Interactive Streamlit UI
just streamlit

# Interactive Terminal CLI
just cli
```

---

## 📂 Repository Structure

- `Intelligent_Student_Support_Agent/app/` — Application source code (Controllers, Services, Models, Routes, Tools, Memory)
- `Intelligent_Student_Support_Agent/evaluation/` — Benchmark evaluation and chunking fidelity auditor
- `Intelligent_Student_Support_Agent/evaluation/results/` — Executive audit reports and benchmark outputs
- `Intelligent_Student_Support_Agent/traces/` — Recorded agent execution traces and tool call logs
- `Intelligent_Student_Support_Agent/data/` — Student handbook PDF and mock seed records
