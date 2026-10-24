# 🛠️ Agent Tools Layer (`app/tools`)

The **Tools Layer** contains executable Python functions that the conversational agent calls dynamically when answering student inquiries. Every tool is instrumented with **ownership guardrails** to prevent unauthorized cross-student data leakage.

---

## 🏗️ Agent Tool Execution Lifecycle

```mermaid
flowchart TD
    Call["LLM Emits Tool Call<br/>e.g. get_fee_status(student_id='STU001')"] --> Guard{"Ownership Guardrail Gatekeeper<br/>check_ownership(caller, target)"}

    Guard -- "caller != target<br/>(Cross-Student Access)" --> Blocked["BLOCKED: Access Denied<br/>• Log immutable event to audit_logs<br/>• Return rejection string to LLM context"]

    Guard -- "caller == target<br/>(Allowed)" --> Allowed["ALLOWED: Target Tool Execution"]

    subgraph ToolSuite["Executable Domain Tools Layer (app/tools/)"]
        direction TB
        Fee["fee_tool.py<br/>• Query fee_records in PostgreSQL<br/>• Total, paid, pending dues, receipt"]
        Schol["scholarship_tool.py<br/>• Query scholarships in PostgreSQL<br/>• Award type, percentage, semester grant"]
        Ticket["ticket_tool.py<br/>• Insert / query support_tickets<br/>• Automatic ticket UUID generation"]
        Profile["profile_tool.py<br/>• Update contact phone, email, address<br/>• Atomic commit in PostgreSQL"]
        Auth["auth_tool.py<br/>• Update student password in DB<br/>• Immediate bcrypt rehash"]
        RAG["rag_tool.py (Sub-Second RAG)<br/>• Qdrant Vector DB Cosine Similarity<br/>• RAM pre-warmed + 24h Redis Cache"]
    end

    Allowed --> Fee
    Allowed --> Schol
    Allowed --> Ticket
    Allowed --> Profile
    Allowed --> Auth
    Allowed --> RAG

    Fee --> Obs["Format String Observation"]
    Schol --> Obs
    Ticket --> Obs
    Profile --> Obs
    Auth --> Obs
    RAG --> Obs
    Blocked --> Obs

    Obs --> Return["Append Observation to Context & Return to Agent ReAct Loop"]
```

---

## 📁 Module Inventory

| File | Tool Functions Exposed | Target Subsystem | Description |
|---|---|---|---|
| [`fee_tool.py`](./fee_tool.py) | `get_fee_status` | PostgreSQL (`fee_records`) | Retrieves tuition fees, amount paid, pending balance, and payment receipts. |
| [`scholarship_tool.py`](./scholarship_tool.py) | `check_scholarship` | PostgreSQL (`scholarships`) | Retrieves active scholarship grants, concession percentages, and semester values. |
| [`ticket_tool.py`](./ticket_tool.py) | `create_support_ticket`, `get_ticket_status`, `list_student_tickets` | PostgreSQL (`support_tickets`) | Creates official support/escalation tickets and looks up resolution statuses. |
| [`profile_tool.py`](./profile_tool.py) | `update_student_profile` | PostgreSQL (`students`) | Updates student contact details (phone, email, campus hostel address) directly. |
| [`auth_tool.py`](./auth_tool.py) | `update_student_password` | PostgreSQL (`auth_credentials`) | Allows students to change their portal login password immediately in the database. |
| [`rag_tool.py`](./rag_tool.py) | `search_student_handbook` | Qdrant Vector DB | Performs dense semantic vector search over student handbook policy chunks. |

---

## 🛡️ Security & Guardrail Guarantees

1. **Identity Binding**: Tools verify that the authenticated caller identity matches the record being accessed or updated.
2. **Immediate Persistence**: State changes (tickets, profile updates, password changes) commit immediately to PostgreSQL within an isolated database transaction.
3. **Structured String Observations**: Tools return natural, well-formatted string summaries that the LLM seamlessly incorporates into its conversational response.
