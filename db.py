import json
import sqlite3
from typing import List, Optional
from models import SpanRecord

DB_NAME = "agent_traces.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spans (
            span_id TEXT PRIMARY KEY,
            trace_id TEXT NOT NULL,
            parent_span_id TEXT,
            name TEXT NOT NULL,
            span_type TEXT NOT NULL,
            status TEXT NOT NULL,
            input_payload TEXT,
            output_payload TEXT,
            error_message TEXT,
            duration_ms REAL,
            tokens_in INTEGER,
            tokens_out INTEGER,
            cost_usd REAL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_span(span: SpanRecord):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            span.span_id,
            span.trace_id,
            span.parent_span_id,
            span.name,
            span.span_type.value,
            span.status.value,
            json.dumps(span.input_payload),
            json.dumps(span.output_payload),
            span.error_message,
            span.duration_ms,
            span.tokens_in,
            span.tokens_out,
            span.cost_usd,
            span.timestamp,
        ),
    )
    conn.commit()
    conn.close()


def get_trace_spans(trace_id: str) -> List[dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM spans WHERE trace_id = ? ORDER BY timestamp ASC",
        (trace_id,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows