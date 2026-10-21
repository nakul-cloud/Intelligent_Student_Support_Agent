"""Comprehensive automated test suite for Task 8: Tracer, Prompts, Client, and Agent Loop.

Validates:
1. Tracer logging, token computation, timing, console rendering, and JSON persistence.
2. System prompt dynamic formatting and rule completeness.
3. Groq client instantiation and decoupling (zero LangSmith coupling).
4. Multi-turn Agent loop execution, tool dispatching, and termination handling.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.agent_loop import run_agent
from app.agent.client import async_groq_client, get_async_groq_client, get_groq_client, groq_client
from app.prompts.system_prompt import SYSTEM_PROMPT_TEMPLATE, build_system_prompt
from app.schemas.tool_schemas import TOOL_MAP, TOOL_SCHEMAS
from tracing.tracer import Tracer


import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def test_system_prompt() -> None:
    """Validate system prompt generation and rule constraints."""
    print("\n--- Testing System Prompt ---")
    default_prompt = build_system_prompt()
    assert "You are the official AI Student Support Agent" in default_prompt
    assert "No prior student memory recorded for this session." in default_prompt
    assert "RULE 1" in default_prompt or "1. GROUNDED IN TRUTH" in default_prompt

    custom_memory = "Student Name: Aarav Sharma | Programme: PGDM AI & DS"
    custom_prompt = build_system_prompt(custom_memory)
    assert custom_memory in custom_prompt
    print("[PASS] System prompt test passed.")


def test_tracer() -> None:
    """Validate Tracer event logging, token aggregation, and JSON persistence."""
    print("\n--- Testing Tracer ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracer = Tracer(agent_name="test_support_agent")
        trace_id = tracer.start("What is my fee status?")
        assert trace_id is not None
        assert len(trace_id) == 8

        # Mock a model response object
        mock_response = MagicMock()
        mock_response.usage.prompt_tokens = 150
        mock_response.usage.completion_tokens = 45
        mock_response.usage.total_tokens = 195
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "get_fee_status"
        mock_response.choices = [MagicMock(message=MagicMock(tool_calls=[mock_tool_call]))]

        # Log events
        tracer.log_model_call(turn=1, response=mock_response, latency_ms=450.2)
        tracer.log_tool_call(
            turn=1,
            tool_name="get_fee_status",
            args={"student_id": "STU001"},
            result="Fee details for STU001: Total INR 450,000",
            latency_ms=12.5,
        )
        tracer.log_retrieval(
            turn=1,
            query="fee refund rules",
            chunks_retrieved=[
                {
                    "content": "Full refund available within 15 days of admission.",
                    "score": 0.88,
                    "metadata": {
                        "document_name": "student_handbook.pdf",
                        "page_number": 7,
                        "heading": "Fee Refund Policy",
                    },
                }
            ],
        )
        tracer.log_termination(turn=2, reason="final_answer")

        # Finish trace and inspect output
        trace_data = tracer.finish(custom_output_dir=tmp_dir)

        assert trace_data["trace_id"] == trace_id
        assert trace_data["total_input_tokens"] == 150
        assert trace_data["total_output_tokens"] == 45
        assert trace_data["total_tokens"] == 195
        assert len(trace_data["trace"]) == 4

        # Verify JSON file was written
        saved_file = Path(tmp_dir) / f"{trace_id}.json"
        assert saved_file.exists()
        with open(saved_file, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
            assert disk_data["trace_id"] == trace_id
            assert disk_data["agent"] == "test_support_agent"

    print("[PASS] Tracer test passed.")


def test_client_decoupling() -> None:
    """Validate client instantiation and absence of direct LangSmith SDK coupling."""
    print("\n--- Testing Groq Client Decoupling ---")
    assert groq_client is not None
    assert async_groq_client is not None
    assert get_groq_client() is groq_client
    assert get_async_groq_client() is async_groq_client

    # Verify no direct vendor wrap_openai imports inside client module
    import app.agent.client as client_module

    assert not hasattr(client_module, "wrap_openai")
    print("[PASS] Groq client decoupling test passed.")


def test_langsmith_adapter() -> None:
    """Validate LangSmithAdapter behavior and SOLID passthrough."""
    print("\n--- Testing LangSmith Adapter (SOLID Decorator) ---")
    from tracing.langsmith_adapter import LangSmithAdapter, langsmith_adapter

    # 1. When disabled in settings, adapter is_enabled() must return False
    assert not langsmith_adapter.is_enabled()

    # 2. wrap_client must act as a transparent passthrough returning the exact same instance
    mock_raw_client = MagicMock()
    result_client = langsmith_adapter.wrap_client(mock_raw_client)
    assert result_client is mock_raw_client

    # 3. Metadata tagger works cleanly
    meta = langsmith_adapter.set_run_metadata(student_id="STU001", role="student_support")
    assert meta["student_id"] == "STU001"
    print("[PASS] LangSmith adapter test passed.")


async def test_agent_loop_with_tool() -> None:
    """Validate agent loop multi-turn execution with mocked LLM tool calling."""
    print("\n--- Testing Agent Loop (Multi-Turn Tool Execution) ---")
    tracer = Tracer()
    tracer.start("What is the fee status for STU001?")

    # Turn 1: Model requests get_fee_status tool call
    mock_tool_call = MagicMock()
    mock_tool_call.id = "call_abc123"
    mock_tool_call.function.name = "get_fee_status"
    mock_tool_call.function.arguments = json.dumps({"student_id": "STU001"})

    mock_msg_turn1 = MagicMock()
    mock_msg_turn1.content = None
    mock_msg_turn1.tool_calls = [mock_tool_call]

    resp_turn1 = MagicMock()
    resp_turn1.choices = [MagicMock(message=mock_msg_turn1)]
    resp_turn1.usage.prompt_tokens = 100
    resp_turn1.usage.completion_tokens = 25
    resp_turn1.usage.total_tokens = 125

    # Turn 2: Model provides final answer
    mock_msg_turn2 = MagicMock()
    mock_msg_turn2.content = "Student STU001 has total tuition fee of INR 450,000 with INR 225,000 pending."
    mock_msg_turn2.tool_calls = None

    resp_turn2 = MagicMock()
    resp_turn2.choices = [MagicMock(message=mock_msg_turn2)]
    resp_turn2.usage.prompt_tokens = 180
    resp_turn2.usage.completion_tokens = 35
    resp_turn2.usage.total_tokens = 215

    # Mock async_groq_client.chat.completions.create to return turn 1 then turn 2
    with patch.object(
        async_groq_client.chat.completions,
        "create",
        AsyncMock(side_effect=[resp_turn1, resp_turn2]),
    ):
        result = await run_agent(
            user_query="What is the fee status for STU001?",
            system_prompt="You are a helpful university agent.",
            tool_schemas=TOOL_SCHEMAS,
            tool_map=TOOL_MAP,
            tracer=tracer,
            max_turns=6,
        )

        trace_data = tracer.finish()

        assert "STU001" in result
        assert "INR" in result
        assert trace_data["total_input_tokens"] == 280
        assert trace_data["total_output_tokens"] == 60
        assert trace_data["total_tokens"] == 340
        # Should have model_call (turn 1), tool_call (turn 1), model_call (turn 2), termination (turn 2)
        assert len(trace_data["trace"]) == 4
        assert trace_data["trace"][1]["type"] == "tool_call"
        assert trace_data["trace"][1]["tool"] == "get_fee_status"
        assert trace_data["trace"][3]["type"] == "termination"
        assert trace_data["trace"][3]["reason"] == "final_answer"

    print("[PASS] Agent loop test passed.")


async def main() -> None:
    """Run all Task 8 tests."""
    print("=" * 60)
    print("TASK 8 VERIFICATION SUITE: Tracer, Prompts, Client, Agent Loop")
    print("=" * 60)

    test_system_prompt()
    test_tracer()
    test_client_decoupling()
    test_langsmith_adapter()
    await test_agent_loop_with_tool()

    print("\n" + "=" * 60)
    print("ALL TASK 8 TESTS PASSED (100% SUCCESS)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
