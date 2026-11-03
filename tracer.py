import functools
import hashlib
import json
import time
import uuid
from typing import Callable, Optional
from db import init_db, insert_span
from models import SpanRecord, SpanStatus, SpanType

# Initialize DB on import
init_db()


class ActiveTraceContext:
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or f"trace_{uuid.uuid4().hex[:10]}"
        self.call_history = []  # Tracks hash of tool + args for loop detection

    def check_loop(self, step_signature: str, max_repeats: int = 3) -> bool:
        self.call_history.append(step_signature)
        if len(self.call_history) >= max_repeats:
            recent = self.call_history[-max_repeats:]
            return all(sig == step_signature for sig in recent)
        return False


def trace_step(
    name: str,
    span_type: SpanType = SpanType.TOOL_CALL,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_usd: float = 0.0,
):
    """Decorator to trace any agent step or tool call."""

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ctx = kwargs.get("_ctx")
            if not ctx or not isinstance(ctx, ActiveTraceContext):
                ctx = ActiveTraceContext()

            span_id = f"span_{uuid.uuid4().hex[:8]}"
            start_time = time.perf_counter()

            # Record arguments (exclude context object)
            clean_kwargs = {k: v for k, v in kwargs.items() if k != "_ctx"}
            input_summary = {"args": [str(a) for a in args], **clean_kwargs}

            # Loop Detection Signature
            sig_payload = f"{name}:{json.dumps(input_summary, sort_keys=True)}"
            sig_hash = hashlib.md5(sig_payload.encode()).hexdigest()

            is_loop = ctx.check_loop(sig_hash, max_repeats=3)
            status = (
                SpanStatus.LOOP_DETECTED if is_loop else SpanStatus.SUCCESS
            )
            error_msg = (
                "Circuit Breaker: Infinite loop detected! Identical tool call repeated 3 times."
                if is_loop
                else None
            )

            result = None
            if not is_loop:
                try:
                    result = func(*args, **clean_kwargs)
                except Exception as e:
                    status = SpanStatus.ERROR
                    error_msg = str(e)
                    raise e
                finally:
                    duration = (time.perf_counter() - start_time) * 1000
                    span = SpanRecord(
                        span_id=span_id,
                        trace_id=ctx.trace_id,
                        name=name,
                        span_type=span_type,
                        status=status,
                        input_payload=input_summary,
                        output_payload=str(result) if result else None,
                        error_message=error_msg,
                        duration_ms=round(duration, 2),
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        cost_usd=cost_usd,
                    )
                    insert_span(span)
            else:
                # Trip breaker - insert failure record without executing
                duration = (time.perf_counter() - start_time) * 1000
                span = SpanRecord(
                    span_id=span_id,
                    trace_id=ctx.trace_id,
                    name=name,
                    span_type=span_type,
                    status=SpanStatus.LOOP_DETECTED,
                    input_payload=input_summary,
                    error_message=error_msg,
                    duration_ms=round(duration, 2),
                )
                insert_span(span)
                raise RuntimeError(error_msg)

            return result

        return wrapper

    return decorator