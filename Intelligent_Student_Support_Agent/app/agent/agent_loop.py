"""Core Multi-Turn Agentic Execution Loop.

Adheres strictly to SOLID Principles:
- Single Responsibility (SRP): Exclusively responsible for orchestrating the multi-turn
  Reasoning-Action (ReAct) cycle between the LLM and registered tools.
- Dependency Inversion (DIP): Depends strictly on high-level contracts:
  - tool_schemas (list of JSON function schemas)
  - tool_map (dictionary mapping tool names to callables)
  - Tracer (observability observer)
  Zero coupling to concrete tool implementations or database models.
- Open/Closed (OCP): New tools and schemas can be introduced to the system
  without modifying a single line of this execution loop.
"""

import asyncio
import json
import time
from typing import Any, Callable, Coroutine
from app.agent.client import async_groq_client
from app.config.settings import settings
from app.providers.llm.factory import LLMFactory
from app.utils.logger import logger
from tracing.tracer import Tracer


async def run_agent(
    user_query: str,
    system_prompt: str,
    tool_schemas: list[dict[str, Any]],
    tool_map: dict[str, Callable[..., Coroutine[Any, Any, str]]],
    tracer: Tracer,
    max_turns: int | None = None,
    conversation_history: list[dict[str, Any]] | None = None,
) -> str:
    """Execute the multi-turn agent loop until a final answer or limit is reached.

    Args:
        user_query: The natural language question or command submitted by the student.
        system_prompt: The fully constructed system prompt containing university rules
                       and injected student memory context.
        tool_schemas: List of OpenAI-compatible function calling specifications.
        tool_map: Dictionary mapping function name strings to executable coroutines.
        tracer: Local Tracer instance to record turn latencies, token consumption,
                tool calls, and termination reasons.
        max_turns: Maximum allowable reasoning-action iterations (defaults to settings.agent_max_turns).
        conversation_history: Optional list of previous turn messages [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        str: The final natural language response synthesized for the student.
    """
    effective_max_turns = max_turns if max_turns is not None else settings.agent_max_turns
    logger.info(f"AgentLoop: Initiating execution loop for query: '{user_query[:60]}...'")

    # 1. Build initial conversation message sequence with system prompt
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
    ]

    # Inject previous conversation history turns (if any)
    if conversation_history:
        for turn_item in conversation_history:
            role = turn_item.get("role")
            content = turn_item.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # Ensure current user_query is the latest user turn
    if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != user_query:
        messages.append({"role": "user", "content": user_query})

    turn = 0

    # 2. Multi-turn reasoning and tool invocation loop
    while turn < effective_max_turns:
        turn += 1
        logger.info(f"AgentLoop: Starting Turn {turn}/{effective_max_turns}...")

        # Measure LLM inference latency
        t_model_start = time.perf_counter()
        try:
            response = await LLMFactory.create_completion_with_fallback(
                messages=messages,
                tools=tool_schemas if tool_schemas else None,
                temperature=settings.agent_temperature,
                client=async_groq_client,
            )
        except Exception as exc:
            t_model_error = (time.perf_counter() - t_model_start) * 1000.0
            logger.error(f"AgentLoop: LLM API request failed at Turn {turn} ({exc})")
            tracer.log_termination(turn=turn, reason=f"error: {type(exc).__name__}")
            return (
                f"I encountered a temporary connection issue while processing your request: {str(exc)}. "
                "Please check your network connection or verify that a valid GROQ_API_KEY is configured in your .env file."
            )

        latency_ms = (time.perf_counter() - t_model_start) * 1000.0

        # Log LLM response metrics into the local tracer
        tracer.log_model_call(turn=turn, response=response, latency_ms=latency_ms)

        choice = response.choices[0]
        assistant_message = choice.message

        # Case A: Model returned tool invocation requests
        if assistant_message.tool_calls:
            logger.info(
                f"AgentLoop: Turn {turn} LLM requested {len(assistant_message.tool_calls)} tool call(s)."
            )

            # Append the assistant message with tool calls to conversation history
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                }
            )

            # Execute each requested tool in order
            for tool_call in assistant_message.tool_calls:
                fn_name = tool_call.function.name
                raw_args = tool_call.function.arguments or "{}"
                tool_call_id = tool_call.id

                # Safely parse JSON arguments produced by the LLM
                try:
                    tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError as json_err:
                    logger.warning(
                        f"AgentLoop: Failed to parse arguments for tool '{fn_name}': {json_err}"
                    )
                    tool_result = f"Error: Invalid JSON arguments provided for tool '{fn_name}'."
                    tool_args = {}
                    tracer.log_tool_call(
                        turn=turn,
                        tool_name=fn_name,
                        args=tool_args,
                        result=tool_result,
                        latency_ms=0.0,
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": fn_name,
                            "content": tool_result,
                        }
                    )
                    continue

                # Look up tool in the dispatch map
                if fn_name not in tool_map:
                    logger.error(f"AgentLoop: Tool '{fn_name}' not found in registered tool_map.")
                    tool_result = f"Error: Tool '{fn_name}' is not recognized or available."
                    tracer.log_tool_call(
                        turn=turn,
                        tool_name=fn_name,
                        args=tool_args,
                        result=tool_result,
                        latency_ms=0.0,
                    )
                else:
                    # Execute tool function and measure latency
                    logger.info(f"AgentLoop: Executing tool '{fn_name}' with args: {tool_args}")
                    t_tool_start = time.perf_counter()
                    try:
                        tool_callable = tool_map[fn_name]
                        if asyncio.iscoroutinefunction(tool_callable):
                            tool_result = await tool_callable(**tool_args)
                        else:
                            tool_result = tool_callable(**tool_args)
                    except Exception as tool_exc:
                        logger.error(
                            f"AgentLoop: Exception raised by tool '{fn_name}': {tool_exc}"
                        )
                        tool_result = f"Error executing tool '{fn_name}': {str(tool_exc)}"

                    tool_latency_ms = (time.perf_counter() - t_tool_start) * 1000.0

                    # Log tool execution to tracer
                    tracer.log_tool_call(
                        turn=turn,
                        tool_name=fn_name,
                        args=tool_args,
                        result=tool_result,
                        latency_ms=tool_latency_ms,
                    )

                # Append tool observation back to conversation history
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": fn_name,
                        "content": str(tool_result),
                    }
                )

            # Continue to next turn so LLM can synthesize tool results
            continue

        # Case B: Model returned a final natural language answer (no tool calls)
        final_answer = assistant_message.content or ""
        logger.info(f"AgentLoop: Final answer generated at Turn {turn}.")
        tracer.log_termination(turn=turn, reason="final_answer")
        return final_answer

    # 3. Maximum turn limit reached without final termination
    logger.warning(
        f"AgentLoop: Exceeded maximum allowed turns ({effective_max_turns}) without final answer."
    )
    tracer.log_termination(turn=turn, reason="max_turns_exceeded")
    return (
        "I apologize, but I could not complete your request within the maximum number of interaction steps. "
        "Please rephrase your query or provide additional details so I can assist you better."
    )
