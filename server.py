from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from db import get_trace_spans, init_db
from models import SpanRecord

app = FastAPI(title="TraceAgent API", version="1.0")

# Enable CORS so your frontend can communicate cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/traces/{trace_id}", response_model=List[dict])
def get_trace(trace_id: str):
    spans = get_trace_spans(trace_id)
    if not spans:
        raise HTTPException(status_code=404, detail="Trace not found")
    return spans


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serves a clean single-file dashboard UI for viewing agent traces."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TraceAgent Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-gray-100 font-sans min-h-screen p-8">
        <div class="max-w-4xl mx-auto">
            <header class="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
                <div>
                    <h1 class="text-2xl font-bold tracking-tight text-emerald-400">⚡ TraceAgent</h1>
                    <p class="text-sm text-gray-400">Autonomous Agent Flight Recorder & Circuit Breaker</p>
                </div>
                <div class="flex gap-2">
                    <input id="traceInput" type="text" placeholder="Enter Trace ID (e.g. trace_...)" 
                           class="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-emerald-500 w-64">
                    <button onclick="fetchTrace()" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition">
                        Load Trace
                    </button>
                </div>
            </header>

            <main id="content" class="space-y-4">
                <div class="text-center py-20 text-gray-500">
                    <p>Enter a Trace ID above to inspect agent steps, timings, and loop detections.</p>
                </div>
            </main>
        </div>

        <script>
            async function fetchTrace() {
                const traceId = document.getElementById('traceInput').value.trim();
                const container = document.getElementById('content');
                if (!traceId) return;

                container.innerHTML = '<p class="text-center text-gray-400 py-10">Loading trace telemetry...</p>';

                try {
                    const res = await fetch(`/api/traces/${traceId}`);
                    if (!res.ok) throw new Error("Trace not found");
                    const spans = await res.json();

                    let html = `<div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
                        <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Execution Timeline (${spans.length} steps)</h2>
                    </div><div class="space-y-3">`;

                    spans.forEach((span, index) => {
                        let statusColor = "border-emerald-500/40 bg-emerald-950/10 text-emerald-400";
                        let badgeBg = "bg-emerald-900/30 text-emerald-300";
                        
                        if (span.status === "error") {
                            statusColor = "border-red-500/40 bg-red-950/10 text-red-400";
                            badgeBg = "bg-red-900/30 text-red-300";
                        } else if (span.status === "loop_detected") {
                            statusColor = "border-amber-500/60 bg-amber-950/20 text-amber-400 animate-pulse";
                            badgeBg = "bg-amber-900/40 text-amber-300";
                        }

                        html += `
                        <div class="border ${statusColor} rounded-xl p-4 flex flex-col gap-2 transition">
                            <div class="flex justify-between items-center">
                                <div class="flex items-center gap-3">
                                    <span class="text-xs font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-400">#${index + 1}</span>
                                    <span class="font-semibold text-gray-200">${span.name}</span>
                                    <span class="text-xs px-2 py-0.5 rounded ${badgeBg}">${span.span_type}</span>
                                </div>
                                <div class="text-xs font-mono text-gray-400 flex gap-4">
                                    <span>⏱️ ${span.duration_ms} ms</span>
                                    <span class="uppercase font-bold">${span.status}</span>
                                </div>
                            </div>
                            ${span.error_message ? `<div class="bg-red-950/40 border border-red-900/50 text-red-300 text-xs p-2.5 rounded font-mono mt-1">⚠️ ${span.error_message}</div>` : ''}
                            <div class="text-xs text-gray-400 font-mono bg-gray-950/50 p-2 rounded mt-1 overflow-x-auto">
                                <span class="text-gray-500">Input:</span> ${span.input_payload}
                            </div>
                        </div>`;
                    });

                    html += `</div>`;
                    container.innerHTML = html;
                } catch (err) {
                    container.innerHTML = `<div class="bg-red-950/20 border border-red-900 text-red-400 p-4 rounded-xl text-center">Trace ID not found in database. Run your test script first to generate a trace!</div>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)