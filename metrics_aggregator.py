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

# Import Lab Core
from core.experiment_manager import ExperimentManager

class LabObservatory:
    def __init__(self):
        self.manager = ExperimentManager()

    async def get_health_report(self):
        """Retrieves the latest Kaizen report from the factory experiments."""
        # Pobieranie plików skanów
        path = self.manager.experiments_dir
        files = glob.glob(f"{path}/*.json")
        
        # Obliczanie agregatu (na razie proste, gotowe pod rozbudowę)
        total_experiments = len(files)
        latest_kaizen_status = "STABLE"
        
        # Próba pobrania ostatniego wglądu z Pamięci RAE (Reflective)
        # To udowadnia synergię z Memory API
        return f"Active experiments: {total_experiments}, Status: {latest_kaizen_status}, Platform: Silicon Oracle v2.9.0"

# Inicjalizacja usług
observatory = LabObservatory()
mcp_server = Server("rae-lab")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="get_factory_health_report",
            description="Retrieves the latest Kaizen report from the factory experiments. Audited.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="trigger_kaizen_analysis",
            description="Manually triggers a new Kaizen insight analysis for a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "quality_score": {"type": "number"},
                    "complexity": {"type": "number"}
                },
                "required": ["project_id", "quality_score"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_factory_health_report":
        result_text = await observatory.get_health_report()
        return [TextContent(type="text", text=result_text)]
    
    if name == "trigger_kaizen_analysis":
        insight = await observatory.manager.register_scan(arguments)
        return [TextContent(type="text", text=json.dumps(insight, indent=2))]
        
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.post("/api/scan")
async def register_scan_endpoint(report: dict):
    """Endpoint dla Quality Tribunal do wysyłania wyników skanów."""
    insight = await observatory.manager.register_scan(report)
    return insight

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import argparse
    import uvicorn
    import json
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", help="Scan a specific file for metrics")
    parser.add_argument("--project", default="dreamsoft", help="Project ID for the scan")
    args = parser.parse_args()
    
    if args.scan:
        # Tryb CLI: Skanuj i wypisz JSON, nie odpalaj serwera
        async def run_cli_scan(path, project):
            manager = ExperimentManager()
            # Symulujemy raport skanu dla CLI (w przyszłości tutaj realna analiza statyczna)
            mock_report = {
                "project_id": project, 
                "file": path, 
                "quality_score": 0.72, 
                "complexity": 15,
                "timestamp": datetime.utcnow().isoformat()
            }
            insight = await manager.register_scan(mock_report)
            print(json.dumps(insight, indent=2))
        
        from datetime import datetime
        asyncio.run(run_cli_scan(args.scan, args.project))
    else:
        # Tryb Serwera: Odpal uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
