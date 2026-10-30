# Evaluation Hub & Benchmark Results

This directory contains audit reports, benchmark measurements, and fidelity evaluations for the **Intelligent Student Support Agent**.

---

## 📊 Evaluation Reports Index

| Evaluation Module | Report File | Target Dimensions / Metrics Tested | Status |
|---|---|---|---|
| **1. Chunking Fidelity Audit** | [📄 `chunking_audit_report.md`](./chunking_audit_report.md) | Text Coverage (100%), Metadata Provenance (100%), Boundary Quality (95.3%), Text Integrity (100%), Table Integrity (100%) | ✅ PASS |
| **2. Auth & Access Control Audit** | [📄 `auth_audit_report.md`](./auth_audit_report.md) | Unenrolled Rejection (100%), Option 2 Registration (100%), Collision Guard (100%), JWT Token Minting (100%), Postgres Isolation (100%) | ✅ PASS |
| **3. Final Evaluation (Assignment 1 vs 2)** | [📄 `final_evaluation_report.md`](./final_evaluation_report.md) | Accuracy (100%), Cross-Tenant Blocking (100%), Approval Gate (100%), Latency, Tokens, Trace Evidence | ✅ PASS |
| **4. Privacy & Approval Architecture** | [📄 `privacy_approval_explanation.md`](./privacy_approval_explanation.md) | Defense-in-depth rules, code-level ownership, approval gate logic, memory scrubbing, and audit schema | ✅ COMPLETE |
| **5. Scenario Benchmark Table** | [📄 `evaluation_table.md`](./evaluation_table.md) | 8 core scenarios runtime latency, tool selection precision, and token telemetry | ✅ PASS |

---

## 🔍 Quick Inspection

To inspect the primary submission deliverables:
- 👉 **[Open Final Evaluation Report: Assignment 1 vs 2 (`final_evaluation_report.md`)](./final_evaluation_report.md)**
- 👉 **[Open Privacy & Approval Rules Explanation (`privacy_approval_explanation.md`)](./privacy_approval_explanation.md)**
- 👉 **[Open Scenario Benchmark Table (`evaluation_table.md`)](./evaluation_table.md)**
- 👉 **[Open Auth & Access Control Audit Report (`auth_audit_report.md`)](./auth_audit_report.md)**
- 👉 **[Open Chunking & Ingestion Fidelity Audit Report (`chunking_audit_report.md`)](./chunking_audit_report.md)**
