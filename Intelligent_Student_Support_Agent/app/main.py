"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config.database import engine, init_db
from app.config.redis import ping_redis, redis_client
from app.config.settings import settings
from app.exceptions.handlers import register_exception_handlers
from app.routes.index import api_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    logger.info(f"Starting Intelligent Student Support Agent ({settings.app_env})...")

    # 1. Verify and initialize PostgreSQL Database
    from app.config.database import check_and_initialize_database
    db_type = await check_and_initialize_database()
    logger.info(f"Database operational backend: {db_type}")

    # 2. Verify Redis connection
    if await ping_redis():
        logger.info("Redis cache connection verified successfully.")
    else:
        logger.warning("Redis connection failed. Cache/memory fallback to PostgreSQL.")

    yield  # Application accepts traffic

    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Database and Redis connections closed cleanly.")


# Create FastAPI instance
app = FastAPI(
    title="Intelligent Student Support Agent API",
    version="1.0.0",
    description="Agentic multi-turn support system with memory, RAG, and PostgreSQL audit tracking.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global custom exception handlers
register_exception_handlers(app)

# Mount API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Service health status endpoint."""
    return {"status": "ok", "app": "Intelligent Student Support Agent", "environment": settings.app_env}


async def _run_cli_loop():
    """Interactive terminal agent CLI session."""
    import sys
    from app.config.database import AsyncSessionLocal
    from app.services.chat_service import ChatService
    from app.memory.memory_manager import MemoryManager

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


def main():
    """Main CLI entrypoint."""
    import argparse
    import asyncio
    import uvicorn

    parser = argparse.ArgumentParser(description="Intelligent Student Support Agent")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI mode")
    parser.add_argument("--host", default=settings.host, help="Bind host for API server")
    parser.add_argument("--port", type=int, default=settings.port, help="Bind port for API server")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable uvicorn hot-reload")

    args = parser.parse_args()

    if args.cli:
        asyncio.run(_run_cli_loop())
    else:
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

