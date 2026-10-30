# Privacy, Permission Control & Approval Rules Architecture

> **Document Type**: Architecture & Policy Specification (Assignment 2 Deliverable)  
> **System**: Intelligent Student Support Agent  
> **Target Audience**: Evaluators, Institutional IT Administrators, Security Auditors  
> **Compliance Target**: Assignment 2 — Safe and Production-Aware Student Support Agent  

---

## 1. Executive Summary & Design Principles

In **Assignment 1**, the Student Support Agent functioned as a capable conversational system that retrieved handbook policies, recalled student facts, and called tools. However, like most prototype agentic systems, it relied heavily on LLM reasoning to decide permissions, making it vulnerable to prompt injection, cross-tenant data leaks, and unintended execution of high-impact mutations.

In **Assignment 2**, we extended the agent into an **enterprise-ready, production-aware support system** by introducing strict **defense-in-depth security controls**:
1. **Deterministic Identity Binding**: Every request is authenticated via signed JWT bearer tokens; student identity is never assumed from conversational text.
2. **Code-Level Ownership Enforcement**: Authorization is enforced in compiled Python service/tool logic (`app/utils/ownership.py`), never delegated to the LLM.
3. **Human-in-the-Loop Approval Gates**: Irreversible or sensitive operations (e.g., fee waiver requests, contact detail mutations) pause for explicit student confirmation before database execution.
4. **Zero-Trust Memory Scrubbing**: Sensitive operational credentials (passwords, OTPs, payment tokens) are deterministically scrubbed before long-term persistence in Redis or PostgreSQL.
5. **Immutable Audit Trail**: All access attempts—whether allowed, blocked, approved, or rejected—are permanently committed to the PostgreSQL `audit_logs` table.

```
                              ┌──────────────────────────────────────────────┐
                              │           Student / Client Request           │
                              └──────────────────────┬───────────────────────┘
                                                     │ (Bearer JWT Token)
                                                     ▼
                              ┌──────────────────────────────────────────────┐
                              │        FastAPI Auth & Identity Layer         │
                              │       (Extracts verified student_id)         │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                                     ▼
                              ┌──────────────────────────────────────────────┐
                              │            Chat & Agent Orchestrator         │
                              └──────┬───────────────────────────────┬───────┘
                                     │                               │
                      [Tool Call]    │                               │  [Fact Persistence]
                                     ▼                               ▼
     ┌─────────────────────────────────────────────────┐   ┌───────────────────────────────────┐
     │           Code-Level Ownership Gate             │   │    Memory Sensitivity Classifier   │
     │      (check_ownership(caller, target))          │   │  (OTPs, Passwords, PINs Scrubbed) │
     └───────┬─────────────────────────────────┬───────┘   └───────────────┬───────────────────┘
             │                                 │                           │
      [Match: ALLOWED]                  [Mismatch: BLOCKED]         [Clean: PERSIST]
             │                                 │                           │
             ▼                                 ▼                           ▼
┌─────────────────────────┐       ┌─────────────────────────┐    ┌───────────────────────────────────┐
│ Sensitive Action Gate?  │       │ Immutable Security Log  │    │  Two-Tier Memory Storage          │
│ (ApprovalService check) │       │ (decision="BLOCKED")    │    │  (Redis L1 + PostgreSQL L2)       │
└──────┬───────────┬──────┘       └─────────────────────────┘    └───────────────────────────────────┘
       │           │
[Yes: PENDING] [No: EXECUTE]
       │           │
       ▼           ▼
┌──────────────┐ ┌──────────────┐
│ Confirmation │ │ Direct Tool  │
│ Gate (YES/NO)│ │ Execution    │
└──────────────┘ └──────────────┘
```

---

## 2. Authentication & Identity Binding

### 2.1 The Invariant
A production support system must never allow a client to "impersonate" another student simply by typing:  
*"I am STU002, what is my fee balance?"*

### 2.2 Implementation
- **JWT Verification**: The student logs in via `POST /api/v1/auth/login` using institutional credentials verified against bcrypt-hashed passwords in `auth_credentials`.
- A signed HS256 JWT is returned containing the claim `sub: "STU001"`.
- The FastAPI dependency `get_current_student` decrypts and validates the token signature on every protected API call.
- **Context Injection**: The verified `student_id` is automatically injected into the request state, the multi-turn agent prompt, and all domain tool arguments via `_build_contextual_tool_map(student_id)`.

---

## 3. Data Privacy & Ownership Rules

### 3.1 The Rule
A student has full read access to their own tuition ledger, scholarship grants, and support tickets, but **zero access** to any other student's records.

### 3.2 Code-Level Enforcement (`ownership.py`)
To prevent LLM jailbreaks or hallucinated permissions, authorization is asserted at the very entry point of every sensitive domain tool:

```python
# app/utils/ownership.py
def check_ownership(requesting_student_id: str, target_student_id: str) -> None:
    req = requesting_student_id.strip().upper()
    target = target_student_id.strip().upper()
    if req != target:
        logger.warning(f"SECURITY ALERT - Cross-student access blocked: {req} attempted to read {target}")
        raise PermissionDeniedError(
            f"Access Denied: Logged-in student '{requesting_student_id}' is not "
            f"authorized to access private records of student '{target_student_id}'."
        )
```

### 3.3 Production Production Examples

#### Example 3A: Allowed Self-Access
- **Student**: `STU001` (authenticated)
- **User Prompt**: *"What is my current fee status and pending balance?"*
- **Tool Triggered**: `get_fee_status(student_id="STU001", requesting_student_id="STU001")`
- **Ownership Check**: `STU001 == STU001` ✅ **MATCH**
- **Outcome**: Tool retrieves tuition ledger from PostgreSQL (`fee_records`).
- **Audit Decision**: `ALLOWED`
- **Response**: Details tuition fee (INR 450,000.00), paid amount (INR 225,000.00), and due date cleanly displayed.

#### Example 3B: Blocked Cross-Student Access
- **Student**: `STU001` (authenticated)
- **User Prompt**: *"Can you check the fee and scholarship records for student STU002?"*
- **Tool Triggered**: `get_fee_status(student_id="STU002", requesting_student_id="STU001")`
- **Ownership Check**: `STU001 != STU002` ❌ **MISMATCH** -> `PermissionDeniedError`
- **Outcome**: Operation immediately aborted; database query never executes.
- **Audit Decision**: `BLOCKED` (Logged with target `STU002`)
- **Response**: *"Access Denied: You are not authorized to view the private fee records of student 'STU002'. Under institutional security guidelines, you may only access your own records."*

---

## 4. Human-in-the-Loop Approval Gate

### 4.1 The Rule
Actions categorized as **sensitive** or **mutative** (such as updating profile contact details, requesting fee waivers, changing sensitive account settings, or submitting disciplinary appeals) must **never execute autonomously** upon the first turn. They require explicit confirmation from the student.

### 4.2 Implementation Architecture (`approval_service.py`)
The system maintains a configurable registry of sensitive actions in `settings.sensitive_actions`:
- `update_contact`
- `request_fee_waiver`
- `update_address`
- `scholarship_appeal`

When an action in this registry is proposed:
1. **Gate Evaluation**: `approval_service.is_sensitive_action(action_name)` returns `True`.
2. **Pending State**: The agent formulates the intended payload, generates an `ApprovalRequest` with `status=ApprovalStatus.PENDING`, and pauses execution.
3. **Confirmation Prompt**: The agent asks the student for explicit confirmation (e.g., *"You have requested to change your contact phone to +91 98765 43210. Please reply 'YES' to confirm or 'NO' to abort."*).
4. **Decision Evaluation**:
   - `YES`, `CONFIRM`, `APPROVE` ➡️ `ApprovalStatus.APPROVED` ➡️ Tool executes and commits changes to DB.
   - `NO`, `CANCEL`, or refusal ➡️ `ApprovalStatus.REJECTED` ➡️ Tool call cancelled, zero DB modifications.

### 4.3 Production Production Examples

#### Example 4A: Approval Required & Approved
- **Turn 1 (Request)**:  
  *Student*: *"I moved to the campus hostel. Please update my address to Room 402, Hostel Block B."*  
  *Agent*: *"I have prepared an update for your residential address to 'Room 402, Hostel Block B'. Because address changes affect official university communications, this action requires confirmation. Do you confirm this update? (Reply YES to proceed or NO to cancel)."*  
  *Audit*: `action=update_address`, `decision=PENDING`
- **Turn 2 (Confirmation)**:  
  *Student*: *"Yes, please update it."*  
  *Agent*: Calls `update_student_profile(student_id="STU001", address="Room 402, Hostel Block B")`.  
  *Audit*: `action=update_address`, `decision=APPROVED`, `result="Updated student contact details: Address: Room 402, Hostel Block B"`  
  *Response*: *"Your address has been successfully updated in the university records."*

#### Example 4B: Approval Rejected by Student
- **Turn 1 (Request)**:  
  *Student*: *"Change my registered emergency mobile number to +91 99999 00000."*  
  *Agent*: *"I have prepared this contact update. Do you confirm updating your emergency phone to +91 99999 00000? (Reply YES or NO)."*
- **Turn 2 (Rejection)**:  
  *Student*: *"No, wait, don't change it yet."*  
  *Agent*: Evaluates response (`NO` -> `REJECTED`). Database mutation is skipped entirely.  
  *Audit*: `action=update_contact`, `decision=REJECTED`, `result="User declined confirmation"`  
  *Response*: *"Action cancelled. Your registered contact information remains unchanged."*

---

## 5. Sensitive Information Scrubbing (Memory Privacy)

### 5.1 The Rule
The student support agent maintains long-term memory across chat sessions for helpful academic context (e.g., enrolled programme, study track, batch year, academic interests). However, **transient and sensitive credentials** (such as temporary passwords, OTPs, CVVs, or bank verification codes) must **never become persistent memory**.

### 5.2 Implementation (`MemoryManager.classify_sensitivity`)
Before any extracted conversation fragment is passed to the persistence layer (Redis L1 or PostgreSQL L2), it is evaluated by `classify_sensitivity()`:

```python
# app/memory/memory_manager.py
def classify_sensitivity(self, text: str) -> Literal["store", "skip"]:
    lowered = text.lower()
    for keyword in self.sensitive_keywords:
        pattern = re.escape(keyword).replace("_", r"[\s_]")
        if re.search(rf"\b{pattern}\b", lowered):
            logger.warning(f"Privacy Guard: Sensitive keyword '{keyword}' detected. Skipping persistence.")
            return "skip"
    return "store"
```

Configured scrubbing keywords (`settings.sensitive_keywords_str`):  
`password,passwd,otp,pin,secret,cvv,token,ssn,credential`

### 5.3 Production Example: Credential Scrubbing
- **User Prompt**: *"My temporary portal password is Password@123 and my SMS OTP is 493012. Please remember this so I don't forget."*
- **Agent Action**:
  1. The LLM acknowledges the message and reminds the student that credentials should never be shared in chat.
  2. Memory extraction pipeline runs: `classify_sensitivity()` catches `password` and `otp`.
  3. Classifier flags the payload as `'skip'`.
  4. **Outcome**: Exactly **0 facts** written to Redis or PostgreSQL `student_memory`.
  5. In subsequent turns or sessions, querying *"What is my password?"* results in the agent correctly stating it does not retain sensitive credentials.

---

## 6. Immutable Audit Trail

### 6.1 Database Schema (`app/models/audit_log.py`)
All security-relevant events write directly to PostgreSQL:

| Column Name | SQL Type | Index | Description |
|:---|:---|:---:|:---|
| `id` | `UUID` (Primary Key) | Yes | Globally unique event identifier |
| `student_id` | `VARCHAR` | Yes | Authenticated student initiating the action |
| `action` | `VARCHAR` | Yes | Target tool or operation (`fee_tool`, `update_contact`, `scholarship_tool`) |
| `target_id` | `VARCHAR` (Nullable) | Yes | The student ID or entity being accessed |
| `decision` | `VARCHAR` | Yes | `ALLOWED`, `BLOCKED`, `APPROVED`, or `REJECTED` |
| `result` | `TEXT` | No | Operational outcome summary or denial reason |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Yes | Tamper-evident UTC timestamp |

### 6.2 Production Audit Trail Records (Sample Database Extract)

```sql
SELECT student_id, action, target_id, decision, result, created_at FROM audit_logs ORDER BY created_at DESC;
```

| student_id | action | target_id | decision | result | created_at (UTC) |
|:---|:---|:---|:---:|:---|:---|
| `STU001` | `fee_tool` | `STU001` | `ALLOWED` | `Fee status retrieved (Status: Partially Paid)` | `2026-10-30 14:10:02` |
| `STU001` | `fee_tool` | `STU002` | `BLOCKED` | `Cross-student private record access denied` | `2026-10-30 14:12:15` |
| `STU001` | `scholarship_tool`| `STU003` | `BLOCKED` | `Cross-student private record access denied` | `2026-10-30 14:15:20` |
| `STU001` | `update_address` | `STU001` | `APPROVED` | `Updated student contact details: Address: Room 402` | `2026-10-30 14:22:41` |
| `STU001` | `fee_waiver` | `STU001` | `REJECTED` | `Student declined confirmation during gate check` | `2026-10-30 14:28:10` |
| `STU001` | `create_ticket` | `STU001` | `ALLOWED` | `Support ticket TICK-06152 opened for IT Facilities` | `2026-10-30 14:35:55` |

---

## 7. Conclusion & Institutional Verification Checklist

| Rubric Requirement | Verification Mechanism | Status |
|:---|:---|:---:|
| **Student identity known** | Verified via signed HS256 JWT claim in FastAPI dependency | ✅ Enforced |
| **Data privacy (own record only)** | Enforced via `check_ownership()` in Python tool code | ✅ Enforced |
| **Non-LLM authorization** | Programmatic guardrail raises `PermissionDeniedError` before DB query | ✅ Enforced |
| **Sensitive action approval** | `ApprovalService` gate triggers confirmation requirement | ✅ Enforced |
| **Rejected actions do not execute** | Negative confirmation branches abort execution with zero mutations | ✅ Enforced |
| **Zero sensitive memory retention** | `MemoryManager.classify_sensitivity` scrubs OTPs/passwords | ✅ Enforced |
| **Immutable audit records** | Every access decision committed to PostgreSQL `audit_logs` | ✅ Enforced |
