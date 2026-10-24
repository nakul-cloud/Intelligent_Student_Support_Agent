# Evaluation Hub & Benchmark Results

This directory contains audit reports, benchmark measurements, and fidelity evaluations for the **Intelligent Student Support Agent**.

---

## 📊 Evaluation Reports Index

| Evaluation Module | Report File | Target Dimensions / Metrics Tested | Status |
|---|---|---|---|
| **1. Chunking Fidelity Audit** | [📄 `chunking_audit_report.md`](./chunking_audit_report.md) | Text Coverage (100%), Metadata Provenance (100%), Boundary Quality (95.3%), Text Integrity (100%), Table Integrity (100%) | ✅ PASS |
| **2. Auth & Access Control Audit** | [📄 `auth_audit_report.md`](./auth_audit_report.md) | Unenrolled Rejection (100%), Option 2 Registration (100%), Collision Guard (100%), JWT Token Minting (100%), Postgres Isolation (100%) | ✅ PASS |
| **3. Semantic Retrieval Benchmark** | `retrieval_benchmark_report.md` | Top-K Recall, MRR, Section Condonation & Policy Clause Retrieval Accuracy | ⏳ Upcoming (Task 12) |
| **4. Agent End-to-End Scenarios** | `agent_scenarios_report.md` | 8 rubric scenarios (Tool Selection, DB Upserts, Profile Memory, Guardrails) | ⏳ Upcoming (Task 12) |
| **5. Memory & Privacy Guardrails** | `memory_audit_report.md` | Sensitive topic redaction (medical, financial, disciplinary) vs durable persistence | ⏳ Upcoming (Task 12) |

---

## 🔍 Quick Inspection

To view the full details of any completed evaluation, click on the respective report file above:
- 👉 **[Open Chunking & Ingestion Fidelity Audit Report (`chunking_audit_report.md`)](./chunking_audit_report.md)**
- 👉 **[Open Identity Authentication & Access Control Audit Report (`auth_audit_report.md`)](./auth_audit_report.md)**
