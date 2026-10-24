"""Local Turn Tracer for Agent Execution, Telemetry, and Security Auditing.

Records detailed turn-by-turn metrics:
- Student identity, conversation, and request correlation IDs
- Dual-tier memory lifecycle (load and save events, sensitive fact redactions)
- LLM inference latency, token consumption (input, output, total), model, and dynamic fallback telemetry
- Code-level ownership guardrail checks and decisions (ALLOWED, BLOCKED, PENDING_APPROVAL)
- Domain tool executions, arguments, observations, and per-tool latencies
- Two-stage RAG retrieval evidence (chunks, page citations, section headings, bi-encoder and re-ranker scores)
- Termination conditions (final_answer, max_turns_exceeded, error, approval_required)
- Outputs formatted console summaries and persists traces to traces/{trace_id}.json
"""

import json
from pathlib import Path
import re
import time
from typing import Any, Optional
import uuid
from datetime import datetime, timezone

from app.config.settings import settings
from app.utils.logger import logger


class Tracer:
    """Captures, logs, and persists full runtime execution traces for the agent.

    Adheres strictly to SOLID Principles:
    - Single Responsibility (SRP): Exclusively manages observability data capture,
      console rendering, and JSON persistence without interfering with core execution logic.
    - Open/Closed (OCP): New event types (e.g. memory_event, guardrail_check) are added
      with standard schemas without breaking downstream consumer expectations.
    """

    def __init__(self, agent_name: str = "student_support_agent") -> None:
        """Initialize a new tracer instance with clean accumulator counters."""
        self.agent_name = agent_name
        self.trace_id: str = ""
        self.student_id: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.request_id: Optional[str] = None
        self.user_input: str = ""
        self.start_perf_counter: float = 0.0
        self.start_timestamp: str = ""
        self.total_latency_ms: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.trace: list[dict[str, Any]] = []
        self.models_used: list[str] = []
        self.fallback_triggered: bool = False
        self.tools_executed: list[str] = []
        self.guardrail_summary: dict[str, int] = {
            "ALLOWED": 0,
            "BLOCKED": 0,
            "PENDING_APPROVAL": 0,
        }
        self.memory_events: list[dict[str, Any]] = []
        self.is_finished: bool = False

    def start(
        self,
        user_query: str,
        trace_id: Optional[str] = None,
        student_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Begin timing a new user turn and initialize trace state."""
        self.trace_id = trace_id or uuid.uuid4().hex[:8]
        self.student_id = student_id
        self.conversation_id = conversation_id
        self.request_id = request_id
        self.user_input = user_query
        self.start_perf_counter = time.perf_counter()
        self.start_timestamp = datetime.now(timezone.utc).isoformat()
        self.total_latency_ms = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.trace = []
        self.models_used = []
        self.fallback_triggered = False
        self.tools_executed = []
        self.guardrail_summary = {"ALLOWED": 0, "BLOCKED": 0, "PENDING_APPROVAL": 0}
        self.memory_events = []
        self.is_finished = False

        ctx_str = f" [Student: {student_id}]" if student_id else ""
        logger.info(
            f"Tracer: Started session [{self.trace_id}]{ctx_str} for query: '{user_query[:60]}...'"
        )
        return self.trace_id

    def log_memory_event(
        self,
        action: str,
        student_id: str,
        count: int,
        keys: list[str],
        latency_ms: float = 0.0,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record dual-tier memory load or save events."""
        event: dict[str, Any] = {
            "action": action,
            "student_id": student_id,
            "count": count,
            "keys": keys,
            "latency_ms": round(latency_ms, 2),
        }
        if details:
            event["details"] = details

        self.memory_events.append(event)
        self.trace.append({
            "turn": 0,
            "type": "memory_event",
            **event,
        })
        logger.debug(f"Tracer: Memory {action} event for student '{student_id}': {count} fact(s)")

    def log_guardrail(
        self,
        turn: int,
        tool_name: str,
        caller_student_id: str,
        target_student_id: Optional[str],
        decision: str,
        reason: str = "",
    ) -> None:
        """Record code-level ownership or sensitive action guardrail evaluation."""
        decision_upper = decision.upper()
        if decision_upper in self.guardrail_summary:
            self.guardrail_summary[decision_upper] += 1
        else:
            self.guardrail_summary[decision_upper] = 1

        record = {
            "turn": turn,
            "type": "guardrail_check",
            "tool": tool_name,
            "caller_student_id": caller_student_id,
            "target_student_id": target_student_id,
            "decision": decision_upper,
            "reason": reason,
        }
        self.trace.append(record)
        logger.debug(
            f"Tracer: Turn {turn} Guardrail on '{tool_name}': {decision_upper} "
            f"(caller={caller_student_id}, target={target_student_id})"
        )

    def log_model_call(
        self,
        turn: int,
        response: Any,
        latency_ms: float,
        model: Optional[str] = None,
        is_fallback: bool = False,
    ) -> None:
        """Record an LLM completion turn, extracting token consumption, model, and requested tools."""
        in_tokens = 0
        out_tokens = 0
        total_tokens = 0

        # Defensively extract token usage metrics
        if hasattr(response, "usage") and response.usage:
            raw_in = getattr(response.usage, "prompt_tokens", 0)
            raw_out = getattr(response.usage, "completion_tokens", 0)
            raw_tot = getattr(response.usage, "total_tokens", 0)
            in_tokens = int(raw_in) if isinstance(raw_in, (int, float)) else 0
            out_tokens = int(raw_out) if isinstance(raw_out, (int, float)) else 0
            total_tokens = int(raw_tot) if isinstance(raw_tot, (int, float)) else (in_tokens + out_tokens)
        elif isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            in_tokens = int(usage.get("prompt_tokens", 0) or 0)
            out_tokens = int(usage.get("completion_tokens", 0) or 0)
            total_tokens = int(usage.get("total_tokens", in_tokens + out_tokens) or 0)

        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens

        # Resolve model name and fallback status safely
        resp_model = (
            getattr(response, "model", None)
            if not isinstance(response, dict)
            else response.get("model")
        )
        if not isinstance(resp_model, str):
            resp_model = None

        resolved_model = (
            model
            if isinstance(model, str)
            else (resp_model if isinstance(resp_model, str) else settings.groq_model)
        )
        fallback_flag = bool(is_fallback or getattr(response, "_is_fallback", False))

        if resolved_model not in self.models_used:
            self.models_used.append(str(resolved_model))
        if fallback_flag:
            self.fallback_triggered = True

        # Extract requested tool names if function calling was triggered
        requested_tools: list[str] = []
        message = None
        if hasattr(response, "choices") and response.choices:
            message = response.choices[0].message
        elif isinstance(response, dict) and "choices" in response and response["choices"]:
            message = response["choices"][0].get("message")

        if message:
            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls is None and isinstance(message, dict):
                tool_calls = message.get("tool_calls")

            if tool_calls and isinstance(tool_calls, (list, tuple)):
                for tc in tool_calls:
                    fn = getattr(tc, "function", None)
                    if fn and hasattr(fn, "name"):
                        fn_name = fn.name
                        if isinstance(fn_name, str):
                            requested_tools.append(fn_name)
                    elif isinstance(tc, dict) and "function" in tc:
                        fn_dict = tc["function"]
                        if isinstance(fn_dict, dict) and "name" in fn_dict:
                            requested_tools.append(str(fn_dict["name"]))

        record = {
            "turn": turn,
            "type": "model_call",
            "model": resolved_model,
            "provider": "groq",
            "is_fallback": fallback_flag,
            "latency_ms": round(latency_ms, 2),
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "total_tokens": total_tokens,
            "requested_tools": requested_tools,
        }
        self.trace.append(record)
        logger.debug(
            f"Tracer: Turn {turn} Model '{resolved_model}' (fallback={fallback_flag}): "
            f"{latency_ms:.1f}ms | Tokens: {total_tokens} | Tools: {requested_tools}"
        )

    def log_tool_call(
        self,
        turn: int,
        tool_name: str,
        args: dict[str, Any],
        result: str,
        latency_ms: float,
        status: str = "success",
        guardrail_status: str = "ALLOWED",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record the execution of a registered domain tool function."""
        if tool_name not in self.tools_executed:
            self.tools_executed.append(tool_name)

        guardrail_upper = (guardrail_status or "ALLOWED").upper()
        if guardrail_upper in self.guardrail_summary:
            self.guardrail_summary[guardrail_upper] += 1
        else:
            self.guardrail_summary[guardrail_upper] = 1

        record: dict[str, Any] = {
            "turn": turn,
            "type": "tool_call",
            "tool": tool_name,
            "arguments": args,
            "observation": result,
            "status": status,
            "guardrail_status": guardrail_upper,
            "latency_ms": round(latency_ms, 2),
        }
        if details:
            record["details"] = details

        self.trace.append(record)
        logger.debug(
            f"Tracer: Turn {turn} Tool '{tool_name}': {latency_ms:.1f}ms | Guardrail: {guardrail_upper}"
        )

        # If this tool was a handbook search, automatically parse and log structured citations
        if tool_name == "search_student_handbook" and result:
            self._extract_and_log_citations(turn=turn, query=args.get("query", ""), text=result)

    def _extract_and_log_citations(self, turn: int, query: str, text: str) -> None:
        """Helper to extract structured citations from handbook search observation text."""
        pattern = re.compile(
            r"\[Citation #(\d+)\s*\|\s*Handbook Section ([^:]+):\s*([^\|]+)\|\s*Page ([^\|]+)\|\s*Relevance:\s*([0-9.-]+)\]",
            re.IGNORECASE,
        )
        matches = pattern.findall(text)
        if not matches:
            return

        evidence_list = []
        for match in matches:
            idx, sec_num, sec_title, page_str, score_str = match
            evidence_list.append({
                "citation_index": int(idx),
                "document": "student_handbook.pdf",
                "section_number": sec_num.strip(),
                "section_title": sec_title.strip(),
                "page": page_str.strip(),
                "score": round(float(score_str.strip()), 4),
            })

        self.log_retrieval(
            turn=turn,
            query=query,
            chunks_retrieved=evidence_list,
            reranker_used=settings.reranker_enabled,
            reranker_model=settings.reranker_model if settings.reranker_enabled else None,
        )

    def log_retrieval(
        self,
        turn: int,
        query: str,
        chunks_retrieved: list[dict[str, Any]],
        reranker_used: bool = False,
        reranker_model: Optional[str] = None,
    ) -> None:
        """Record RAG policy retrieval evidence for audits."""
        evidence_list = []
        for chunk in chunks_retrieved:
            if "citation_index" in chunk:
                evidence_list.append(chunk)
            else:
                meta = chunk.get("metadata", {})
                evidence_list.append({
                    "document": meta.get("document_name", "student_handbook.pdf"),
                    "section_number": meta.get("section_number", "N/A"),
                    "section_title": meta.get("section_title", meta.get("heading", "Policy Section")),
                    "page": meta.get("page_number", 0),
                    "score": round(float(chunk.get("score", 0.0)), 4),
                    "bi_encoder_score": round(float(chunk.get("bi_encoder_score", chunk.get("score", 0.0))), 4),
                    "snippet": (chunk.get("content", "")[:140] + "...").replace("\n", " "),
                })

        record = {
            "turn": turn,
            "type": "retrieval",
            "query": query,
            "chunks_count": len(chunks_retrieved),
            "reranker_used": reranker_used,
            "reranker_model": reranker_model,
            "evidence": evidence_list,
        }
        self.trace.append(record)
        logger.debug(
            f"Tracer: Turn {turn} Retrieval: {len(chunks_retrieved)} chunks for '{query[:40]}' "
            f"(reranker={reranker_used})"
        )

    def log_termination(self, turn: int, reason: str, details: Optional[str] = None) -> None:
        """Record the reason why the agent concluded its multi-turn execution."""
        record: dict[str, Any] = {
            "turn": turn,
            "type": "termination",
            "reason": reason,
        }
        if details:
            record["details"] = details
        self.trace.append(record)
        logger.info(f"Tracer: Terminated at turn {turn} (Reason: {reason})")

    def finish(self, custom_output_dir: Optional[str] = None) -> dict[str, Any]:
        """Finalize the trace, compute cumulative metrics, print summary, and save to JSON."""
        if not self.is_finished:
            elapsed_sec = time.perf_counter() - self.start_perf_counter
            self.total_latency_ms = round(elapsed_sec * 1000.0, 2)
            self.is_finished = True

        trace_data: dict[str, Any] = {
            "trace_id": self.trace_id,
            "student_id": self.student_id,
            "conversation_id": self.conversation_id,
            "request_id": self.request_id,
            "agent": self.agent_name,
            "timestamp": self.start_timestamp or datetime.now(timezone.utc).isoformat(),
            "user_input": self.user_input,
            "total_latency_ms": self.total_latency_ms,
            "duration_ms": self.total_latency_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "models_used": self.models_used,
            "fallback_triggered": self.fallback_triggered,
            "tools_executed": self.tools_executed,
            "guardrail_summary": self.guardrail_summary,
            "memory_events": self.memory_events,
            "turn_count": len([s for s in self.trace if s.get("type") in ("model_call", "tool_call")]),
            "steps": self.trace,
            "trace": self.trace,
        }

        # Resolve target trace file directory defensively
        if custom_output_dir:
            out_dir = Path(custom_output_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent
            out_dir = project_root / settings.traces_dir

        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / f"{self.trace_id}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Tracer: Persisted trace JSON to '{file_path}'.")
        except Exception as exc:
            logger.error(f"Tracer: Failed to persist trace JSON to '{file_path}': {exc}")

        # Render console summary table for user and professor verification
        self._print_console_summary(trace_data)

        return trace_data

    def _print_console_summary(self, data: dict[str, Any]) -> None:
        """Render a formatted, clean ASCII summary block to the log output."""
        border = "=" * 76
        sub_border = "-" * 76

        models_list = [str(m) for m in data.get("models_used", []) if m]
        models_str = ", ".join(models_list) or settings.groq_model
        fallback_str = "YES (Qwen 2.5 32B)" if data.get("fallback_triggered") else "No (Primary OK)"
        student_str = str(data.get("student_id") or "N/A")
        tools_list = [str(t) for t in data.get("tools_executed", []) if t]
        tools_str = ", ".join(tools_list) or "None"

        summary_lines = [
            border,
            f"  AGENT TURN TRACE SUMMARY | ID: {data['trace_id']}",
            border,
            f"  Student ID     : {student_str}",
            f"  User Query     : {data['user_input']}",
            f"  Total Latency  : {data['total_latency_ms']:.1f} ms",
            f"  Total Tokens   : {data['total_tokens']} (Prompt: {data['total_input_tokens']}, Output: {data['total_output_tokens']})",
            f"  Models Used    : {models_str} [Fallback Triggered: {fallback_str}]",
            f"  Tools Run      : {tools_str}",
            f"  Guardrails     : {data.get('guardrail_summary', {})}",
            sub_border,
            "  Turn-by-Turn Execution Timeline:",
        ]

        for step in data.get("trace", []):
            turn = step.get("turn", 0)
            step_type = step.get("type", "unknown")

            if step_type == "model_call":
                tools = step.get("requested_tools", [])
                tools_req = ", ".join(tools) if tools else "None (Final Answer)"
                fb_tag = " [FALLBACK]" if step.get("is_fallback") else ""
                summary_lines.append(
                    f"    [Turn {turn}] Model Call : {step.get('model', 'Groq')}{fb_tag} | "
                    f"{step.get('latency_ms', 0):.1f}ms | Tokens: {step.get('total_tokens', 0)} | Requested: [{tools_req}]"
                )
            elif step_type == "guardrail_check":
                summary_lines.append(
                    f"    [Turn {turn}] Guardrail  : {step.get('tool')} -> {step.get('decision')} (caller={step.get('caller_student_id')})"
                )
            elif step_type == "tool_call":
                summary_lines.append(
                    f"    [Turn {turn}] Tool Exec  : {step.get('tool')} ({step.get('latency_ms', 0):.1f}ms) | Status: {step.get('status')}"
                )
            elif step_type == "retrieval":
                rerank_info = f" (Reranker: {step.get('reranker_model', 'None')})" if step.get("reranker_used") else ""
                summary_lines.append(
                    f"    [Turn {turn}] RAG Search : {step.get('chunks_count', 0)} citation chunks retrieved{rerank_info}"
                )
            elif step_type == "memory_event":
                summary_lines.append(
                    f"    [Memory] {step.get('action').upper()}     : {step.get('count', 0)} facts for student '{step.get('student_id')}'"
                )
            elif step_type == "termination":
                summary_lines.append(
                    f"    [Turn {turn}] Terminated : {step.get('reason')}"
                )

        summary_lines.append(border)
        summary_text = "\n" + "\n".join(summary_lines)
        logger.info(summary_text)
