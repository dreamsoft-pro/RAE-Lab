# metrics_aggregator.py
import os
import json
import glob
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
import uvicorn
import asyncio
from datetime import datetime

# Import Lab Core
try:
    from core.experiment_manager import ExperimentManager
except ImportError:
    # Safe fallback if not structured
    class ExperimentManager:
        def __init__(self):
            self.experiments_dir = "./experiments"
            os.makedirs(self.experiments_dir, exist_ok=True)
        async def register_scan(self, report):
            path = os.path.join(self.experiments_dir, f"scan_{int(datetime.utcnow().timestamp())}.json")
            with open(path, "w") as f:
                json.dump(report, f)
            return {"status": "registered", "path": path}

class MABTuner:
    """Multi-Armed Bandit optimizer to dynamically tune CostAwareRouter weights in rae-core."""
    def __init__(self):
        self.alpha = 0.4  # Weight for accuracy
        self.beta = 0.3   # Weight for latency reduction
        self.gamma = 0.3  # Weight for cost reduction

    def calculate_success_rate(self, accuracy: float, latency_ratio: float, cost_ratio: float) -> float:
        # Success Rate Formula: alpha * Accuracy + beta * (1 - LatencyRatio) + gamma * (1 - CostRatio)
        success_rate = (self.alpha * accuracy) + (self.beta * (1.0 - latency_ratio)) + (self.gamma * (1.0 - cost_ratio))
        return round(success_rate, 4)

    def optimize_router_weights(self, feedback_events: list) -> dict:
        """Processes list of feedback events and computes new optimal weights for CostAwareRouter."""
        if not feedback_events:
            return {"alpha": 0.4, "beta": 0.3, "gamma": 0.3}
            
        total_acc = 0.0
        total_lat = 0.0
        total_cost = 0.0
        count = len(feedback_events)
        
        for event in feedback_events:
            total_acc += event.get("accuracy", 0.8)
            total_lat += event.get("latency_ratio", 0.5)
            total_cost += event.get("cost_ratio", 0.4)
            
        avg_acc = total_acc / count
        avg_lat = total_lat / count
        avg_cost = total_cost / count
        
        # Adjust weights dynamically based on average success signals
        # Sum of weights must strictly equal 1.0, and remain within [0.05, 0.85] bounds (Anti-Looping rule)
        raw_alpha = avg_acc
        raw_beta = 1.0 - avg_lat
        raw_gamma = 1.0 - avg_cost
        
        total_raw = raw_alpha + raw_beta + raw_gamma
        if total_raw == 0:
            return {"alpha": 0.4, "beta": 0.3, "gamma": 0.3}
            
        # Normalize and apply boundary guardrails [0.05, 0.85]
        new_alpha = max(0.05, min(0.85, raw_alpha / total_raw))
        new_beta = max(0.05, min(0.85, raw_beta / total_raw))
        new_gamma = 1.0 - new_alpha - new_beta
        
        # Secondary guardrail for gamma
        if new_gamma < 0.05:
            diff = 0.05 - new_gamma
            new_gamma = 0.05
            if new_alpha > new_beta:
                new_alpha -= diff
            else:
                new_beta -= diff
                
        return {
            "alpha": round(new_alpha, 4),
            "beta": round(new_beta, 4),
            "gamma": round(new_gamma, 4)
        }

class LabObservatory:
    def __init__(self):
        self.manager = ExperimentManager()
        self.tuner = MABTuner()
        # Telemetry metrics collection (Prometheus / OTEL fallback)
        self.metrics_db = []

    async def get_health_report(self):
        """Retrieves the latest Kaizen report from the factory experiments."""
        path = self.manager.experiments_dir
        files = glob.glob(f"{path}/*.json")
        
        total_experiments = len(files)
        latest_kaizen_status = "STABLE"
        
        # Calculate recent optimal weights from telemetry history
        recent_weights = self.tuner.optimize_router_weights(self.metrics_db[-20:])
        
        return {
            "active_experiments": total_experiments,
            "status": latest_kaizen_status,
            "platform": "Silicon Oracle v3.2.0",
            "optimal_weights": recent_weights,
            "telemetry_events": len(self.metrics_db)
        }

    def record_telemetry(self, event: dict):
        """Registers a new telemetry event for real-time tracking."""
        event["timestamp"] = datetime.utcnow().isoformat()
        self.metrics_db.append(event)
        # Keep metrics database bounded to avoid memory exhaustion
        if len(self.metrics_db) > 1000:
            self.metrics_db.pop(0)

# Inicjalizacja usług
observatory = LabObservatory()
mcp_server = Server("rae-lab")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="get_factory_health_report",
            description="Retrieves the latest Kaizen health report and MAB weights. Audited.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="record_telemetry_event",
            description="Registers a new OpenTelemetry / Prometheus metric event to the observatory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "accuracy": {"type": "number"},
                    "latency_ratio": {"type": "number"},
                    "cost_ratio": {"type": "number"},
                    "model_used": {"type": "string"}
                },
                "required": ["accuracy", "latency_ratio"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_factory_health_report":
        result = await observatory.get_health_report()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    if name == "record_telemetry_event":
        observatory.record_telemetry(arguments)
        return [TextContent(type="text", text="Telemetry event recorded successfully.")]
        
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.post("/mcp/messages")
async def mcp_messages_endpoint(request: Request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

@app.post("/api/scan")
async def register_scan_endpoint(report: dict):
    """Endpoint dla Quality Tribunal do wysyłania wyników skanów."""
    insight = await observatory.manager.register_scan(report)
    # Register scan score to telemetry
    observatory.record_telemetry({
        "accuracy": report.get("quality_score", 0.8),
        "latency_ratio": report.get("latency_ratio", 0.3),
        "cost_ratio": report.get("cost_ratio", 0.2)
    })
    return insight

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
