# core/experiment_manager.py
import json
import os
import httpx
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from rae_libs.rae_core.utils.memory_bridge import RAEMemoryBridge
from rae_libs.rae_core.utils.context import RAEContextLocator

logger = logging.getLogger(__name__)

class ExperimentManager:
    """Advanced Lab Manager for Kaizen Insights and Factory Metrics (DeepMind standard)."""
    
    def __init__(self, storage_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = storage_path or os.getenv("RAE_LAB_STORAGE", os.path.join(base_dir, "storage"))
        self.experiments_dir = os.path.join(self.storage_path, "experiments")
        self.api_url = os.getenv("RAE_API_URL", "http://rae-api-dev:8000")
        os.makedirs(self.experiments_dir, exist_ok=True)
        
        # Unified Bridge with Advanced Labeling
        self.bridge = RAEMemoryBridge(project_name="rae-lab")

    async def register_scan(self, report_data: Dict[str, Any]):
        """Registers a quality scan with deep metadata enrichment."""
        project = report_data.get("project", "unknown")
        
        # 1. Advanced Metrics Calculation (Deep Lab Logic)
        quality_score = report_data.get("quality_score", 0.0)
        complexity = report_data.get("complexity", 0)
        lean_score = round(quality_score / (1 + (complexity / 100)), 2) # Example: Advanced Lean Metric
        
        enriched_data = {
            **report_data,
            "kaizen_metrics": {
                "lean_score": lean_score,
                "complexity_index": complexity,
                "stability_index": 0.95 # Placeholder for future logic
            },
            "swarm_id": os.getenv("RAE_SWARM_ID", "default_evolution")
        }

        # 2. Unified Audit with Rich Human Label
        self.bridge.log_decision(
            action="scan_registered",
            reasoning=f"Skan jakości dla {project}. Lean Score: {lean_score}. Complexity: {complexity}.",
            payload=enriched_data
        )
        
        return await self.generate_kaizen_insight(project, enriched_data)

    async def generate_kaizen_insight(self, project: str, current_scan: Dict[str, Any]):
        """Generates a Kaizen Insight based on historical trends (RAE-First)."""
        try:
            # 1. RAE-First Retrieval
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                    "query": f"kaizen metrics history for {project}",
                    "project": project,
                    "k": 5
                })
                history = resp.json().get("results", []) if resp.status_code == 200 else []

            # 2. Trend Analysis (Advanced)
            current_lean = current_scan.get("kaizen_metrics", {}).get("lean_score", 0.0)
            prev_leans = [float(h.get("metadata", {}).get("context", {}).get("kaizen_metrics", {}).get("lean_score", 0)) 
                          for h in history if "kaizen_metrics" in h.get("metadata", {}).get("context", {})]
            
            avg_lean = sum(prev_leans) / len(prev_leans) if prev_leans else current_lean
            trend = "up" if current_lean >= avg_lean else "down"
            
            insight = {
                "project": project,
                "timestamp": datetime.utcnow().isoformat(),
                "swarm_id": current_scan.get("swarm_id"),
                "kaizen_metrics": current_scan.get("kaizen_metrics"),
                "trend": trend,
                "suggestion": self._derive_kaizen_suggestion(current_scan, trend)
            }
            
            # 3. Permanent Insight Persistence (The "Advanced" part)
            # Storing as a proper KAIZEN_REPORT type
            self.bridge.save_event(
                content=f"Wniosek Kaizen dla {project}: {insight['suggestion']}",
                human_label=f"Wniosek Kaizen: {project} ({trend.upper()})",
                layer="reflective",
                metadata={
                    "type": "kaizen_report",
                    "project": project,
                    "metrics": insight["kaizen_metrics"],
                    "trend": trend
                }
            )
            
            return insight

        except Exception as e:
            logger.error(f"Kaizen analysis failed: {e}")
            return {"status": "error", "message": str(e)}

    def _derive_kaizen_suggestion(self, scan: Dict[str, Any], trend: str) -> str:
        metrics = scan.get("kaizen_metrics", {})
        if metrics.get("lean_score", 1.0) < 0.5:
            return "KRYTYCZNE: Kod jest 'tłusty' (niski Lean Score). Wymagana dekompozycja."
        if trend == "down":
            return "OSTRZEŻENIE: Wykryto spadek wydajności inżynieryjnej."
        return "STABILNIE: Doskonała optymalizacja procesów."
