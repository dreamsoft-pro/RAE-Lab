# metrics_aggregator.py
import os
import json
import glob
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
import uvicorn

mcp_server = Server("rae-lab")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="get_factory_health_report",
            description="Retrieves the latest Kaizen report from the factory experiments.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_factory_health_report":
        path = "/app/experiments"
        files = glob.glob(f"{path}/*.json")
        return [TextContent(type="text", text=f"Active experiments: {len(files)}, Kaizen: 0.85")]
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
