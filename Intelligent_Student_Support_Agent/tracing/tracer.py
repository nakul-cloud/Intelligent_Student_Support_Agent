"""Local Turn Tracer for Agent Execution and Auditing.

Records detailed turn-by-turn metrics:
- LLM inference latency and token consumption (input, output, total)
- Tool call requests, arguments, observations, and tool latencies
- RAG retrieval evidence (source documents, pages, section headings, scores)
- Termination conditions (final_answer, max_turns_exceeded, error)
- Outputs formatted console summaries and persists traces to traces/{trace_id}.json
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from app.config.settings import settings
from app.utils.logger import logger


class Tracer:
    """Captures, logs, and persists full runtime execution traces for the agent.

    Adheres to the Single Responsibility Principle (SRP):
    Exclusively manages observability data capture, console rendering,
    and JSON persistence without interfering with core agent execution logic.
    """

    def __init__(self, agent_name: str = "student_support_agent") -> None:
        """Initialize a new tracer instance with clean accumulator counters."""
        self.agent_name = agent_name
        self.trace_id: str = ""
        self.user_input: str = ""
        self.start_perf_counter: float = 0.0
        self.start_timestamp: str = ""
        self.total_latency_ms: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.trace: list[dict[str, Any]] = []
        self.is_finished: bool = False

    def start(self, user_query: str, trace_id: Optional[str] = None) -> str:
        """Begin timing a new user turn and initialize trace state.

        Args:
            user_query: The incoming natural language query from the student.
            trace_id: Optional pre-existing trace ID; if None, generates an 8-character hex UUID.

        Returns:
            str: The unique identifier for this trace session.
        """
        self.trace_id = trace_id or uuid.uuid4().hex[:8]
        self.user_input = user_query
        self.start_perf_counter = time.perf_counter()
        self.start_timestamp = datetime.now(timezone.utc).isoformat()
        self.total_latency_ms = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.trace = []
        self.is_finished = False

        logger.info(
            f"Tracer: Started session [{self.trace_id}] for query: '{user_query[:60]}...'"
        )
        return self.trace_id

    def log_model_call(
        self,
        turn: int,
        response: Any,
        latency_ms: float,
    ) -> None:
        """Record an LLM completion turn, extracting token consumption and requested tools.

        Args:
            turn: The 1-indexed turn number within the agentic loop.
            response: The ChatCompletion response object returned by the model.
            latency_ms: The execution duration in milliseconds.
        """
        in_tokens = 0
        out_tokens = 0
        total_tokens = 0

        # Defensively extract token usage metrics across OpenAI/Groq response objects
        if hasattr(response, "usage") and response.usage:
            in_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            out_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            total_tokens = getattr(response.usage, "total_tokens", in_tokens + out_tokens) or 0
        elif isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            in_tokens = usage.get("prompt_tokens", 0)
            out_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", in_tokens + out_tokens)

        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens

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

            if tool_calls:
                for tc in tool_calls:
                    fn = getattr(tc, "function", None)
                    if fn and hasattr(fn, "name"):
                        requested_tools.append(fn.name)
                    elif isinstance(tc, dict) and "function" in tc:
                        requested_tools.append(tc["function"].get("name", "unknown"))

        record = {
            "turn": turn,
            "type": "model_call",
            "latency_ms": round(latency_ms, 2),
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "total_tokens": total_tokens,
            "requested_tools": requested_tools,
        }
        self.trace.append(record)
        logger.debug(
            f"Tracer: Turn {turn} Model Call: {latency_ms:.1f}ms | Tokens: {total_tokens} | Tools: {requested_tools}"
        )

    def log_tool_call(
        self,
        turn: int,
        tool_name: str,
        args: dict[str, Any],
        result: str,
        latency_ms: float,
    ) -> None:
        """Record the execution of a registered tool function.

        Args:
            turn: The 1-indexed turn number.
            tool_name: Name of the executed tool function.
            args: The dictionary of arguments passed into the tool.
            result: The string result or observation returned by the tool.
            latency_ms: Execution duration of the tool in milliseconds.
        """
        record = {
            "turn": turn,
            "type": "tool_call",
            "tool": tool_name,
            "arguments": args,
            "observation": result,
            "latency_ms": round(latency_ms, 2),
        }
        self.trace.append(record)
        logger.debug(
            f"Tracer: Turn {turn} Tool '{tool_name}': {latency_ms:.1f}ms | Args: {args}"
        )

    def log_retrieval(
        self,
        turn: int,
        query: str,
        chunks_retrieved: list[dict[str, Any]],
    ) -> None:
        """Record RAG policy retrieval evidence for assignment audits.

        Args:
            turn: The turn number during which retrieval took place.
            query: The semantic search query string.
            chunks_retrieved: List of chunk dictionaries containing content and metadata.
        """
        evidence_list = []
        for chunk in chunks_retrieved:
            meta = chunk.get("metadata", {})
            evidence_list.append(
                {
                    "document": meta.get("document_name", "student_handbook.pdf"),
                    "page": meta.get("page_number", 0),
                    "heading": meta.get("heading", "Policy Section"),
                    "score": round(float(chunk.get("score", 0.0)), 3),
                    "snippet": (chunk.get("content", "")[:120] + "...").replace("\n", " "),
                }
            )

        record = {
            "turn": turn,
            "type": "retrieval",
            "query": query,
            "chunks_count": len(chunks_retrieved),
            "evidence": evidence_list,
        }
        self.trace.append(record)
        logger.debug(f"Tracer: Turn {turn} Retrieval: {len(chunks_retrieved)} chunks for '{query[:40]}'")

    def log_termination(self, turn: int, reason: str) -> None:
        """Record the reason why the agent concluded its multi-turn execution.

        Args:
            turn: The final turn number.
            reason: Termination code ('final_answer', 'max_turns_exceeded', 'error').
        """
        record = {
            "turn": turn,
            "type": "termination",
            "reason": reason,
        }
        self.trace.append(record)
        logger.info(f"Tracer: Terminated at turn {turn} (Reason: {reason})")

    def finish(self, custom_output_dir: Optional[str] = None) -> dict[str, Any]:
        """Finalize the trace, compute cumulative metrics, print summary, and save to JSON.

        Args:
            custom_output_dir: Optional directory override for saving the JSON trace file.
                              Defaults to project 'traces/' directory.

        Returns:
            dict[str, Any]: The complete serialized trace object.
        """
        if not self.is_finished:
            elapsed_sec = time.perf_counter() - self.start_perf_counter
            self.total_latency_ms = round(elapsed_sec * 1000.0, 2)
            self.is_finished = True

        trace_data: dict[str, Any] = {
            "trace_id": self.trace_id,
            "agent": self.agent_name,
            "timestamp": self.start_timestamp or datetime.now(timezone.utc).isoformat(),
            "user_input": self.user_input,
            "total_latency_ms": self.total_latency_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "trace": self.trace,
        }

        # Resolve target trace file directory defensively
        if custom_output_dir:
            out_dir = Path(custom_output_dir)
        else:
            # Resolve to Intelligent_Student_Support_Agent / settings.traces_dir
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent
            out_dir = project_root / settings.traces_dir

        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / f"{self.trace_id}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Tracer: Persisted trace JSON to '{file_path}'.")
        except Exception as exc:
            logger.error(f"Tracer: Failed to persist trace JSON to '{file_path}': {exc}")

        # Render console summary table for user and professor verification
        self._print_console_summary(trace_data)

        return trace_data

    def _print_console_summary(self, data: dict[str, Any]) -> None:
        """Render a formatted, clean ASCII summary block to the log output."""
        border = "=" * 70
        sub_border = "-" * 70

        summary_lines = [
            border,
            f"  AGENT TURN TRACE SUMMARY | ID: {data['trace_id']}",
            border,
            f"  User Query     : {data['user_input']}",
            f"  Total Latency  : {data['total_latency_ms']:.1f} ms",
            f"  Input Tokens   : {data['total_input_tokens']}",
            f"  Output Tokens  : {data['total_output_tokens']}",
            f"  Total Tokens   : {data['total_tokens']}",
            sub_border,
            "  Execution Timeline:",
        ]

        for step in data.get("trace", []):
            turn = step.get("turn", 0)
            step_type = step.get("type", "unknown")

            if step_type == "model_call":
                tools = step.get("requested_tools", [])
                tools_str = ", ".join(tools) if tools else "None (Final Answer Generation)"
                summary_lines.append(
                    f"    [Turn {turn}] Model Call : {step.get('latency_ms', 0):.1f}ms | "
                    f"Tokens: {step.get('total_tokens', 0)} | Requested: [{tools_str}]"
                )
            elif step_type == "tool_call":
                summary_lines.append(
                    f"    [Turn {turn}] Tool Exec  : {step.get('tool')} ({step.get('latency_ms', 0):.1f}ms)"
                )
            elif step_type == "retrieval":
                summary_lines.append(
                    f"    [Turn {turn}] Retrieval  : Retrieved {step.get('chunks_count', 0)} policy chunks"
                )
            elif step_type == "termination":
                summary_lines.append(
                    f"    [Turn {turn}] Terminated : {step.get('reason')}"
                )

        summary_lines.append(border)
        summary_text = "\n" + "\n".join(summary_lines)
        logger.info(summary_text)
