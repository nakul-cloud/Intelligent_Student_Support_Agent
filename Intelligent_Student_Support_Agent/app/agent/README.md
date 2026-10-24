# 🤖 Agent Loop & LLM Client (`app/agent`)

The **Agent Layer** manages the execution cycle of the AI Student Support Agent, LLM inference dispatch via Groq, iterative function-calling resolution, and real-time execution trace assembly.

---

## 🏗️ Multi-Turn Agent Loop Lifecycle

```mermaid
flowchart TD
    Start["Inbound Student Turn<br/>• User Query + Dual-Tier Memory Context"] --> Init["1. Initialize Turn Context<br/>• Assemble System Prompt & Student Facts<br/>• Bind AGENT_TOOLS Schemas<br/>• Initialize LocalTurnTracer"]
    Init --> Infer["2. LLM Inference via LLMFactory<br/>• Primary Model: settings.groq_model<br/>• Fallback Model: settings.groq_fallback_model (qwen/qwen3.8-27b)"]

    Infer --> Decision{"LLM Decision"}

    Decision -- "Emits Tool Calls" --> Dispatch["3. Tool Dispatcher (app/tools/)<br/>• check_ownership(caller, target)<br/>• fee, scholarship, ticket, or rag_tool"]
    
    Dispatch --> Gate{"Ownership & Action Gate"}
    Gate -- "Cross-Student Access" --> Block["BLOCKED: Security Audit Log<br/>Observation: Access Denied"]
    Gate -- "Sensitive Action" --> Suspend["SUSPEND: pending_approval = True<br/>Awaiting Student Confirmation"]
    Gate -- "Allowed" --> ExecTool["Execute Tool against DB / Vector Store<br/>Format Observation String"]

    Block --> ContextUpdate["Append Tool Observation to Messages"]
    ExecTool --> ContextUpdate
    ContextUpdate --> LoopGuard{"Iteration < max_turns (6)?"}
    LoopGuard -- "Yes" --> Infer
    LoopGuard -- "Max Turns Reached" --> FinalFallback["Synthesize Best-Effort Explanation"]

    Decision -- "Emits Text Answer" --> Citations["4. Citation & Output Processing<br/>• Match Page & Section Provenance<br/>• Extract Non-Sensitive Facts for Memory"]
    FinalFallback --> Citations
    Suspend --> Citations

    Citations --> Result["5. Return ChatResponse<br/>• message, conversation_id, trace_id<br/>• facts_learned, pending_approval, trace metrics"]
```

---

## 📁 Module Inventory

| File | Core Component | Role & Functionality |
|---|---|---|
| [`agent_loop.py`](./agent_loop.py) | `run_agent_turn` | Executes the iterative ReAct-style loop: manages message history, calls the LLM via `LLMFactory` with dynamic fallback (`qwen/qwen3.8-27b`), executes requested database/RAG tools, and enforces loop termination. |
| [`client.py`](./client.py) | `get_async_groq_client`, `get_groq_client` | Delegates client provisioning to `app/providers/llm/factory.py` and `GroqProvider`, exposing fallback-enabled `AsyncOpenAI` instances pointed to the Groq API endpoint. |

---

## 💎 Robustness & Termination Guards

1. **Max Turn Cap**: The agent loop is hard-bounded (default: 5 iterations) to prevent infinite looping or runaway API costs.
2. **Graceful Fallback**: If an individual tool encounters a database exception, the error string is formatted as an observation rather than crashing the turn, allowing the LLM to explain the issue clearly to the student.
3. **Observability Tracking**: Records model latency, token usage (input/output/total), tool arguments, and execution durations in structured turn traces.
