from models import SpanType
from tracer import ActiveTraceContext, trace_step


# Define traced tools
@trace_step(name="lookup_order", span_type=SpanType.TOOL_CALL)
def lookup_order(order_id: str):
    return {"order_id": order_id, "status": "delayed"}


@trace_step(name="fetch_customer_email", span_type=SpanType.TOOL_CALL)
def fetch_customer_email(order_id: str):
    return "customer@example.com"


# Simulate an agent run with a single trace context
def run_broken_agent():
    ctx = ActiveTraceContext()
    print(f"Starting Agent with Trace ID: {ctx.trace_id}\n")

    # Normal step
    lookup_order("10482", _ctx=ctx)

    # Agent enters a loop (e.g., repeatedly querying the same missing email)
    print("Simulating agent repetitive loop...")
    try:
        for _ in range(5):
            fetch_customer_email("10482", _ctx=ctx)
    except RuntimeError as err:
        print(f"\n[ALERT] Circuit Breaker Caught Error: {err}")


if __name__ == "__main__":
    run_broken_agent()