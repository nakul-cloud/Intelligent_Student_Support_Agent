# 🧠 Dual-Tier Memory System (`app/memory`)

The **Memory Layer** manages conversational state and long-term user preferences across multiple turns and sessions. It implements a **privacy-first, dual-tier architecture** combining low-latency ephemeral cache with durable, scrubbed persistence.

---

## 🏗️ Dual-Tier Memory Architecture

```mermaid
flowchart TD
    Turn["User Prompt & Turn Interaction"] --> Tier1["Tier 1: Redis Ephemeral Memory (L1)<br/>• Key: 'conv:{conversation_id}'<br/>• TTL: 24 Hours<br/>• Low-latency sliding window for conversational continuity"]

    Tier1 --> PrivacyGate{"Privacy & Redaction Gate<br/>(app/memory/memory_manager.py)"}

    PrivacyGate -- "Sensitive Categories Detected<br/>• Passwords, PINs, OTPs, CVVs, tokens<br/>• Medical / Health conditions<br/>• Bank account & card numbers<br/>• Disciplinary / Legal grievances" --> Scrub["SCRUB & DISCARD<br/>Never written to persistent disk"]

    PrivacyGate -- "Allowed Student Facts<br/>• Academic interests & goals<br/>• Preferred topics & study habits" --> Tier2[("Tier 2: PostgreSQL Durable Store (L2)<br/>• Table: 'student_memory'<br/>• Idempotent upsert via pg_insert<br/>• Long-term recall across sessions")]

    Tier1 -.-> AgentContext["Injected into System Prompt Context"]
    Tier2 -.-> AgentContext
```

---

## 📁 Module Inventory

| File | Core Component | Role & Functionality |
|---|---|---|
| [`memory_manager.py`](./memory_manager.py) | `MemoryManager` | Orchestrates the two-tier lifecycle: loads active context from Redis, filters sensitive topics, extracts durable facts, and injects context into the system prompt. |
| [`redis_memory.py`](./redis_memory.py) | `RedisMemoryStore` | Manages fast JSON-serialized conversation sliding windows in Redis with TTL expiration. |
| [`postgres_memory.py`](./postgres_memory.py) | `PostgresMemoryStore` | Durable PostgreSQL repository performing idempotent key-value fact persistence (`student_memory` table) via native `pg_insert`. |

---

## 🔒 Privacy Scrubbing Categories

The `MemoryManager` strictly scrubs and blocks the following topic categories before writing to PostgreSQL:
- **Medical / Mental Health**: Illness, prescriptions, counseling, disability status.
- **Disciplinary / Legal**: Suspensions, fines, disciplinary committee actions, pending grievances.
- **Financial Details**: Bank account numbers, UPI IDs, fee debt amounts (fees remain strictly in `fee_records`).
- **Authentication Secrets**: Passwords, PINs, OTPs, API keys.
