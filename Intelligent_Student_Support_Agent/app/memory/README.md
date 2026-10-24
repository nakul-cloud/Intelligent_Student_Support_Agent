# 🧠 Dual-Tier Memory System (`app/memory`)

The **Memory Layer** manages conversational state and long-term user preferences across multiple turns and sessions. It implements a **privacy-first, dual-tier architecture** combining low-latency ephemeral cache with durable, scrubbed persistence.

---

## 🏗️ Dual-Tier Memory Architecture

```
[ User Prompt & Turn Interaction ]
                │
                ▼
┌───────────────────────────────────────────────┐
│     Tier 1: Redis Ephemeral Memory            │  <-- app/memory/redis_memory.py
│  - Key: "conv:{conversation_id}"              │
│  - TTL: 24 Hours                              │  Stores last 10 turns of raw turn-by-turn
│  - Low latency sliding window                 │  dialogue for active context continuity.
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│     Privacy & Sensitive Fact Redaction Gate   │  <-- app/memory/memory_manager.py
├───────────────────────────────────────────────┤
│ Blocks and scrubs sensitive categories:       │  Prevents private or confidential data
│ - Medical / Health conditions                 │  from leaking into durable long-term storage.
│ - Disciplinary records & active grievances    │
│ - Passwords & authentication tokens           │
│ - Bank accounts & financial balances          │
└───────────────────────┬───────────────────────┘
                        │ (Allowed non-sensitive facts only)
                        ▼
┌───────────────────────────────────────────────┐
│     Tier 2: PostgreSQL Durable Memory Store   │  <-- app/memory/postgres_memory.py
│  - Table: student_memory                      │
│  - Idempotent upsert (on_conflict_do_update)  │  Persists student preferences, career goals,
│  - Cross-session persistent recall            │  and academic focus across logins.
└───────────────────────────────────────────────┘
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
