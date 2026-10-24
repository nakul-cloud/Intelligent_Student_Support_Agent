# 🗄️ Relational Models Layer (`app/models`)

The **Models Layer** defines the persistent PostgreSQL relational schema using SQLAlchemy 2.0 Declarative Async Mappings (`Mapped`, `mapped_column`). All tables operate strictly inside the PostgreSQL Docker database container with zero SQLite dependencies.

---

## 🏗️ Entity Relationship Diagram (PostgreSQL)

```mermaid
erDiagram
    students ||--o| fee_records : "has one ledger"
    students ||--o| scholarships : "awarded"
    students ||--o| auth_credentials : "authenticates via"
    students ||--o{ support_tickets : "files"
    students ||--o{ conversations : "initiates"
    conversations ||--o{ messages : "contains"
    students ||--o{ student_memory : "remembers facts"
    students ||--o{ audit_logs : "audits actions"

    students {
        UUID id PK
        string student_id UK
        string name
        string programme
        string batch
        string phone
        string email
        string address
        string status
    }

    fee_records {
        UUID id PK
        string student_id FK
        float total_fee
        float paid
        float pending
        string due_date
        string status
        string receipt
    }

    scholarships {
        UUID id PK
        string student_id FK
        string scholarship_type
        float percentage
        float amount_per_semester
        string status
    }

    auth_credentials {
        UUID id PK
        string student_id UK
        string hashed_password
    }

    support_tickets {
        UUID id PK
        string ticket_id UK
        string student_id FK
        string category
        string description
        string priority
        string status
        datetime created_at
    }

    conversations {
        UUID id PK
        string student_id FK
        string title
        string status
        datetime created_at
    }

    messages {
        UUID id PK
        UUID conversation_id FK
        string role
        string content
        jsonb meta_data
        datetime created_at
    }

    student_memory {
        UUID id PK
        string student_id FK
        string key
        string value
        string category
        datetime updated_at
    }

    audit_logs {
        UUID id PK
        string student_id
        string action
        string target_id
        string decision
        string result
        datetime created_at
    }
```

---

## 📁 Module Inventory

| File | Tables Defined | Description |
|---|---|---|
| [`base.py`](./base.py) | `Base`, `BaseModel` | Declarative Base with automatic `UUID` primary keys and UTC `created_at` / `updated_at` timestamp mixins. |
| [`student_records.py`](./student_records.py) | `students`, `fee_records`, `scholarships`, `support_tickets` | Core university enterprise records: student profiles, tuition ledgers, scholarship awards, and support escalation tickets. |
| [`auth_credentials.py`](./auth_credentials.py) | `auth_credentials` | Stores student login credentials with bcrypt hashed passwords. |
| [`conversation.py`](./conversation.py) | `conversations` | Multi-turn conversational session container linked to student identity. |
| [`message.py`](./message.py) | `messages` | Turn-by-turn prompts, assistant replies, token counts, and step traces using PostgreSQL `JSONB`. |
| [`student_memory.py`](./student_memory.py) | `student_memory` | Durable long-term student facts (career goals, preferences, academic interests) extracted during conversations. |
| [`audit_log.py`](./audit_log.py) | `audit_logs` | Immutable security audit trail recording tool invocations, access decisions, and policy blocks. |
| [`document.py`](./document.py) | `documents` | Ingested PDF document metadata, page counts, chunk tracking, and processing status. |

---

## 💎 Model Principles & Integrity

1. **Pure PostgreSQL JSONB**: Rich metadata in `messages` and `documents` utilizes native PostgreSQL `JSONB` for indexing and query performance.
2. **Referential Integrity**: Cascading deletes (`ondelete="CASCADE"`) guarantee that removing a test student cleans up associated fee records and conversation sessions cleanly.
3. **Immutability of Audit Trails**: `audit_logs` records are append-only to maintain regulatory compliance.
