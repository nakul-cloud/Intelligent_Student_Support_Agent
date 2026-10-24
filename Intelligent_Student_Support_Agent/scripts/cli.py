"""Interactive terminal agent CLI runner.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively manages interactive terminal CLI input/output.
"""

import asyncio
import sys
from app.config.database import AsyncSessionLocal
from app.memory.memory_manager import MemoryManager
from app.services.chat_service import ChatService


async def run_cli():
    """Interactive terminal agent CLI session."""
    print("\n" + "=" * 70)
    print("  INTELLIGENT STUDENT SUPPORT AGENT — INTERACTIVE TERMINAL CLI")
    print("  Two-Tier Memory | RAG Handbook | PostgreSQL | Audit Logging")
    print("=" * 70)
    print("Commands: 'exit'/'quit' to leave, 'switch' to change student ID, 'mem' to inspect memory.\n")

    current_student_id = input("Enter Student ID [default: STU001]: ").strip().upper() or "STU001"
    conv_id = None

    async with AsyncSessionLocal() as session:
        chat_service = ChatService(session)
        memory_mgr = MemoryManager(session)

        # Show initial memory context
        facts = await memory_mgr.load_memory(current_student_id)
        print(f"\n[Active Student: {current_student_id}]")
        print(f"[Loaded Memory Context]:\n{facts}\n")

        while True:
            try:
                user_input = input(f"[{current_student_id}] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession ended.")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("Exiting CLI session. Goodbye!")
                break

            if user_input.lower() == "switch":
                new_id = input("Enter new Student ID: ").strip().upper()
                if new_id:
                    current_student_id = new_id
                    conv_id = None
                    facts = await memory_mgr.load_memory(current_student_id)
                    print(f"Switched to {current_student_id}. Memory loaded:\n{facts}\n")
                continue

            if user_input.lower() == "mem":
                facts = await memory_mgr.load_memory(current_student_id)
                print(f"\n--- Stored Facts for {current_student_id} ---\n{facts}\n")
                continue

            # Run agent turn
            try:
                print("Thinking...", end="\r", flush=True)
                resp = await chat_service.chat(
                    student_id=current_student_id,
                    message=user_input,
                    conversation_id=conv_id,
                    debug=True,
                )
                conv_id = resp.conversation_id
                print(f"\nAgent:\n{resp.reply}\n")
                if resp.trace:
                    t = resp.trace
                    tools_used = [s.get("tool_name") for s in t.get("steps", []) if s.get("type") == "tool_call"]
                    latency_ms = t.get("duration_ms", 0)
                    tokens = t.get("total_tokens", 0)
                    print(f"--- [Trace: {latency_ms:.1f}ms | {tokens} tokens | tools: {tools_used}] ---\n")
            except Exception as e:
                print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(run_cli())
