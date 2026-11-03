from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SpanType(str, Enum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    PLANNING = "planning"


class SpanStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    LOOP_DETECTED = "loop_detected"


class SpanRecord(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    span_type: SpanType
    status: SpanStatus = SpanStatus.SUCCESS
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[Any] = None
    error_message: Optional[str] = None
    duration_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )