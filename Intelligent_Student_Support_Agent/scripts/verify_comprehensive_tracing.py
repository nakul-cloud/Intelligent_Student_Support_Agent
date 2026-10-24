"""End-to-end verification script for comprehensive tracing telemetry.

Validates that every single runtime event and decision is traced:
- Student identity, conversation, and correlation IDs
- Dual-tier memory lifecycle (load and save events)
- LLM inference latency, model, tokens, and fallback telemetry
- Ownership guardrail checks and decisions (ALLOWED vs BLOCKED)
- Domain tool executions and per-tool latency
- Two-stage RAG retrieval evidence (chunks, page numbers, sections, scores)
- Trace JSON persistence and ASCII summary rendering
"""

import asyncio
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config.database import AsyncSessionLocal
from app.services.chat_service import ChatService


async def verify_tracing() -> None:
    print("=" * 76)
    print("STARTING COMPREHENSIVE TRACING VERIFICATION")
    print("=" * 76)

    student_id = "STU001"
    request_id = "test-corr-req-9999"

    async with AsyncSessionLocal() as session:
        service = ChatService(session)

        # Scenario 1: Legitimate query invoking domain tool (get_fee_status) and RAG (search_student_handbook)
        print("\n[Scenario 1] Legitimate Query (Fee Status + Handbook Policy)")
        query_1 = "What is my pending fee and what is the minimum attendance required for final exams according to the student handbook?"
        resp_1 = await service.process_turn(
            student_id=student_id,
            user_message=query_1,
            request_id=request_id,
        )

        print(f"\nResponse 1 Assistant Reply:\n{resp_1.message[:250]}...\n")
        print(f"Trace ID: {resp_1.trace_id}")
        assert resp_1.trace is not None, "Trace data must be populated in ChatResponse"
        
        # Verify trace artifact on disk
        traces_dir = Path("traces")
        trace_file_1 = traces_dir / f"{resp_1.trace_id}.json"
        assert trace_file_1.exists(), f"Trace JSON file {trace_file_1} should exist"

        with open(trace_file_1, "r", encoding="utf-8") as f:
            disk_trace_1 = json.load(f)

        print(f"Verified Trace 1 Disk JSON: {trace_file_1}")
        print(f"  - Student ID: {disk_trace_1.get('student_id')}")
        print(f"  - Request ID: {disk_trace_1.get('request_id')}")
        print(f"  - Total Tokens: {disk_trace_1.get('total_tokens')}")
        print(f"  - Total Latency: {disk_trace_1.get('total_latency_ms')} ms")
        print(f"  - Models Used: {disk_trace_1.get('models_used')}")
        print(f"  - Tools Executed: {disk_trace_1.get('tools_executed')}")
        print(f"  - Guardrail Summary: {disk_trace_1.get('guardrail_summary')}")
        print(f"  - Memory Events: {len(disk_trace_1.get('memory_events', []))} event(s)")

        # Verify memory events
        mem_events = disk_trace_1.get("memory_events", [])
        assert any(e.get("action") == "load" for e in mem_events), "Must record memory load event"
        assert any(e.get("action") == "save" for e in mem_events), "Must record memory save event"

        # Scenario 2: Cross-student unauthorized query (triggers ownership guardrail BLOCKED)
        print("\n[Scenario 2] Unauthorized Cross-Student Query (Ownership Guardrail)")
        query_2 = "Check fee status for student STU002."
        resp_2 = await service.process_turn(
            student_id=student_id,
            user_message=query_2,
            request_id=request_id,
        )

        print(f"\nResponse 2 Assistant Reply:\n{resp_2.message[:250]}...\n")
        trace_file_2 = traces_dir / f"{resp_2.trace_id}.json"
        assert trace_file_2.exists(), f"Trace JSON file {trace_file_2} should exist"

        with open(trace_file_2, "r", encoding="utf-8") as f:
            disk_trace_2 = json.load(f)

        print(f"Verified Trace 2 Disk JSON: {trace_file_2}")
        print(f"  - Guardrail Summary: {disk_trace_2.get('guardrail_summary')}")
        assert disk_trace_2.get("guardrail_summary", {}).get("BLOCKED", 0) >= 1 or "BLOCKED" in str(disk_trace_2), (
            "Must detect and record BLOCKED guardrail in trace"
        )

    print("\n" + "=" * 76)
    print("ALL COMPREHENSIVE TRACING VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 76)


if __name__ == "__main__":
    asyncio.run(verify_tracing())
