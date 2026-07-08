import json
import time
import asyncio

from app.config import settings
from app.context import get_injected_fault
from app.observability.logger import get_logger
from app.observability.metrics import AI_INFERENCE_DURATION_SECONDS, AI_TOKEN_USAGE_TOTAL, APP_EXCEPTIONS_TOTAL
from app.schemas.tools import CreateTicketToolInput
from app.services.ticket_service import create_incident_ticket
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

logger = get_logger("app.services.ai_engine")

# Definition of the tool exposed to the LLM
TICKET_TOOL_DEFINITION: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "create_incident_ticket",
        "description": (
            "Create a DevOps/SRE incident ticket when a system alert or error query indicates "
            "an actionable infrastructure issue."
        ),
        "parameters": CreateTicketToolInput.model_json_schema(),
    },
}


async def process_ask_request(question: str, context: dict[str, object] | None = None) -> dict[str, object]:
    """
    Processes a natural language DevOps/SRE query using an AI Tool-Calling workflow.
    Supports fault injection, multi-provider execution (Gemini/OpenRouter/OpenAI), and mock fallback.
    """
    start_time = time.perf_counter()
    fault = get_injected_fault()

    # 1. Fault Injection Testing Support
    if fault == "llm_timeout":
        logger.error(
            "Simulating injected LLM timeout fault",
            extra={"event": "ai_inference_fault_injected", "metadata": {"fault": fault}}
        )
        APP_EXCEPTIONS_TOTAL.labels(exception_type="TimeoutError", endpoint="/ask").inc()
        await asyncio.sleep(0.3)
        raise TimeoutError("Simulated LLM Provider Timeout (Injected Fault: llm_timeout)")

    if fault == "llm_error":
        logger.error(
            "Simulating injected LLM API error fault",
            extra={"event": "ai_inference_fault_injected", "metadata": {"fault": fault}}
        )
        APP_EXCEPTIONS_TOTAL.labels(exception_type="RuntimeError", endpoint="/ask").inc()
        raise RuntimeError("Simulated LLM Provider Error (Injected Fault: llm_error)")

    # Determine execution provider
    model_used = "mock-sre-engine-v1"
    status = "success"

    try:
        if not settings.force_mock_mode and (settings.gemini_api_key or settings.openrouter_api_key or settings.openai_api_key):
            result = await _run_live_llm_tool_loop(question, context)
            model_used = result["model_used"]
        else:
            result = await _run_mock_tool_loop(question, context)
            model_used = "mock-sre-engine-v1"

        duration_sec = time.perf_counter() - start_time
        duration_ms = round(duration_sec * 1000, 2)

        AI_INFERENCE_DURATION_SECONDS.labels(model=model_used, status=status).observe(duration_sec)

        logger.info(
            f"AI inference and tool workflow completed successfully in {duration_ms}ms",
            extra={
                "event": "ai_inference_completed",
                "duration_ms": duration_ms,
                "metadata": {
                    "model": model_used,
                    "tokens_used": result.get("tokens_used", 0),
                    "business_action_triggered": result.get("business_action") is not None
                }
            }
        )
        result["execution_metadata"] = {
            "model_used": model_used,
            "tokens_used": result.get("tokens_used", 0),
            "processing_time_ms": duration_ms
        }
        return result

    except Exception as exc:
        duration_sec = time.perf_counter() - start_time
        AI_INFERENCE_DURATION_SECONDS.labels(model=model_used, status="error").observe(duration_sec)
        APP_EXCEPTIONS_TOTAL.labels(exception_type=type(exc).__name__, endpoint="/ask").inc()
        logger.exception(
            f"AI inference execution failed: {exc}",
            extra={"event": "ai_inference_failed", "metadata": {"model": model_used}}
        )
        raise


async def _run_live_llm_tool_loop(question: str, context: dict[str, object] | None) -> dict[str, object]:
    """Runs live OpenAI SDK tool-calling loop against configured provider."""
    from openai import OpenAI

    if settings.gemini_api_key:
        client = OpenAI(
            api_key=settings.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        model = settings.gemini_model_name
    elif settings.openrouter_api_key:
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        model = settings.openrouter_model_name
    else:
        client = OpenAI(api_key=settings.openai_api_key)
        model = settings.openai_model_name

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "You are an SRE/DevOps AI assistant. Analyze infrastructure issues or questions. "
                "If the query involves an actionable incident or alert, call create_incident_ticket."
            )
        },
        {"role": "user", "content": f"Question: {question}\nContext: {json.dumps(context or {})}"}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=[TICKET_TOOL_DEFINITION],
        tool_choice="auto",
        temperature=0.1
    )

    assistant_message = response.choices[0].message
    tokens_prompt = int(getattr(response.usage, "prompt_tokens", 50))
    tokens_completion = int(getattr(response.usage, "completion_tokens", 40))

    AI_TOKEN_USAGE_TOTAL.labels(model=model, token_type="prompt").inc(tokens_prompt)
    AI_TOKEN_USAGE_TOTAL.labels(model=model, token_type="completion").inc(tokens_completion)

    business_action: dict[str, object] | None = None

    if assistant_message.tool_calls:
        tool_call = assistant_message.tool_calls[0]
        if tool_call.type == "function":
            raw_args = str(tool_call.function.arguments)
            validated_args = CreateTicketToolInput.model_validate_json(raw_args)

            business_action = create_incident_ticket(
                service=validated_args.service,
                severity=validated_args.severity,
                summary=validated_args.summary,
                recommended_action=validated_args.recommended_action,
            )

            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": str(tc.function.arguments),
                        },
                    }
                    for tc in assistant_message.tool_calls
                    if tc.type == "function"
                ],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(business_action)
            })

            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1
            )
            summary_text = str(final_response.choices[0].message.content or "")
            tokens_completion += int(getattr(final_response.usage, "completion_tokens", 30))
        else:
            summary_text = str(assistant_message.content or "")
    else:
        summary_text = str(assistant_message.content or "")

    result: dict[str, object] = {
        "question": question,
        "ai_analysis": {
            "summary": summary_text,
            "root_cause_hypothesis": "Analyzed via live AI tool-calling workflow.",
            "recommended_action": str(business_action["recommended_action"]) if business_action and "recommended_action" in business_action else "Monitor system metrics."
        },
        "business_action": business_action,
        "model_used": model,
        "tokens_used": tokens_prompt + tokens_completion
    }
    return result


async def _run_mock_tool_loop(question: str, context: dict[str, object] | None) -> dict[str, object]:
    """Deterministic simulation of the Pydantic tool-calling loop for dependable testing."""
    await asyncio.sleep(0.15)  # Simulate network inference latency

    # Inspect question to simulate intelligent triage
    q_lower = question.lower()
    is_high_severity = any(kw in q_lower for kw in ["memory", "cpu", "leak", "crash", "down", "error", "alert"])
    severity = "HIGH" if is_high_severity else "MEDIUM"
    service_name = (context or {}).get("service", "worker-service")

    # Simulate Pydantic tool argument validation
    raw_args = json.dumps({
        "service": service_name,
        "severity": severity,
        "summary": f"Incident detected: {question[:80]}",
        "recommended_action": "Rollback deployment to stable tag and inspect heap dump."
    })
    validated_args = CreateTicketToolInput.model_validate_json(raw_args)

    # Execute business action tool
    business_action = create_incident_ticket(
        service=validated_args.service,
        severity=validated_args.severity,
        summary=validated_args.summary,
        recommended_action=validated_args.recommended_action,
    )

    AI_TOKEN_USAGE_TOTAL.labels(model="mock-sre-engine-v1", token_type="prompt").inc(64)
    AI_TOKEN_USAGE_TOTAL.labels(model="mock-sre-engine-v1", token_type="completion").inc(78)

    return {
        "question": question,
        "ai_analysis": {
            "summary": f"AI Triage Assessment for service '{service_name}': Potential resource degradation or anomaly detected.",
            "root_cause_hypothesis": "Recent commit or configuration drift caused unconstrained resource consumption.",
            "recommended_action": business_action["recommended_action"]
        },
        "business_action": business_action,
        "model_used": "mock-sre-engine-v1",
        "tokens_used": 142
    }
