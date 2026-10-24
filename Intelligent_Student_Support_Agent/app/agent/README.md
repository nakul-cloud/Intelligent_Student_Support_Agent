# 🤖 Agent Loop & LLM Client (`app/agent`)

The **Agent Layer** manages the execution cycle of the AI Student Support Agent, LLM inference dispatch via Groq, iterative function-calling resolution, and real-time execution trace assembly.

---

## 🏗️ Multi-Turn Agent Loop Lifecycle

```
[ Inbound Student Prompt + Dual-Tier Memory Facts ]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Initialize Turn Context                     │
│  - Assemble System Prompt + Injected Student Memories       │
│  - Attach JSON Tool Schemas (AGENT_TOOLS)                   │
│  - Open Turn Tracer (LocalTurnTracer & optional LangSmith)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│             Inference Call to Groq LLM API                  │
│       (app/agent/client.py -> AsyncOpenAI wire protocol)     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼ (LLM Requests Tool Calls)     ▼ (LLM Emits Final Answer)
┌──────────────────────────────────┐ ┌─────────────────────────┐
│     Execute Tool Dispatcher      │ │    Assemble Citations   │
│  - Verify Ownership Security     │ │  - Page references      │
│  - Execute PostgreSQL/Qdrant Tool│ │  - Ledger receipts      │
│  - Append Observation to Context │ └────────────┬────────────┘
└────────────────┬─────────────────┘              │
                 │                                ▼
                 └──────► [ Re-invoke LLM ]  [ Return ChatResponse ]
                          (Max 5 iterations)
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
