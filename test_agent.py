from models import SpanType
from tracer import ActiveTraceContext, trace_step


@trace_step(
    name="llm_agent_reasoning",
    span_type=SpanType.LLM_CALL,
    model_name="gpt-4o",
    tokens_in=1200,
    tokens_out=350,
)
def llm_agent_reasoning(prompt: str):
    return "Decision: Query order lookup tool."


@trace_step(
    name="lookup_order", span_type=SpanType.TOOL_CALL, model_name="local-ollama"
)
def lookup_order(order_id: str):
    return {"order_id": order_id, "status": "delayed"}


@trace_step(
    name="fetch_customer_email",
    span_type=SpanType.TOOL_CALL,
    model_name="gpt-4o",
    tokens_in=400,
    tokens_out=80,
)
def fetch_customer_email(order_id: str):
    return "customer@example.com"


def run_broken_agent():
    ctx = ActiveTraceContext()
    print(f"Starting Agent with Trace ID: {ctx.trace_id}\n")

    # LLM reasoning step with token costs
    llm_agent_reasoning("Check status for order 10482", _ctx=ctx)
    lookup_order("10482", _ctx=ctx)

    # Simulating a looping tool call
    print("Simulating agent repetitive loop...")
    try:
        for _ in range(5):
            fetch_customer_email("10482", _ctx=ctx)
    except RuntimeError as err:
        print(f"\n[ALERT] Circuit Breaker Caught Error: {err}")


if __name__ == "__main__":
    run_broken_agent()