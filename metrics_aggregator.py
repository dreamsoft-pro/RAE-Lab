# metrics_aggregator.py
import os
import json
import glob
from fastapi import FastAPI
import uvicorn
import asyncio

app = FastAPI(title="RAE-Lab API")

@app.get("/report")
def get_report():
    path = "/app/experiments"
    files = glob.glob(f"{path}/*.json")
    return {"total_experiments": len(files), "status": "active"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🔬 RAE-Lab Intelligence Observatory ONLINE")
    uvicorn.run(app, host="0.0.0.0", port=8000)
