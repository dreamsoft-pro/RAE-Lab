# core/experiment_manager.py
import json
import os
import httpx
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ExperimentManager:
    """Zarządza wynikami audytów i wyciąga wnioski Kaizen z Pamięci RAE."""
    
    def __init__(self, storage_path: Optional[str] = None):
        # RAE-Path-Refactor: Use environment or default relative to current module
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = storage_path or os.getenv("RAE_LAB_STORAGE", os.path.join(base_dir, "storage"))
        self.experiments_dir = os.path.join(self.storage_path, "experiments")
        self.api_url = os.getenv("RAE_API_URL", "http://rae-api-dev:8000")
        os.makedirs(self.experiments_dir, exist_ok=True)

    async def register_scan(self, report_data: Dict[str, Any]):
        """Zapisuje skan i wywołuje analizę trendu."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        project = report_data.get("project_id", "unknown")
        filename = f"scan_{project}_{timestamp}.json"
        
        path = os.path.join(self.experiments_dir, filename)
        with open(path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Wyzwalanie asynchronicznej analizy Kaizen
        return await self.generate_kaizen_insight(project, report_data)

    async def generate_kaizen_insight(self, project_id: str, current_scan: Dict[str, Any]):
        """Analizuje trend jakości na podstawie Pamięci RAE."""
        try:
            # 1. Pobieranie historycznych skanów z Pamięci RAE (Warstwa Semantic)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                    "query": f"quality scan for project {project_id}",
                    "project": project_id,
                    "k": 5
                })
                history = resp.json().get("results", []) if resp.status_code == 200 else []

            # 2. Obliczanie trendu (prosta logika na początek, gotowa pod LLM)
            current_score = current_scan.get("quality_score", 0.0)
            prev_scores = [float(h.get("metadata", {}).get("score", 0)) for h in history if "score" in h.get("metadata", {})]
            
            avg_prev = sum(prev_scores) / len(prev_scores) if prev_scores else current_score
            trend = "up" if current_score >= avg_prev else "down"
            
            insight = {
                "project": project_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "current_score": current_score,
                    "avg_historical": avg_prev,
                    "trend": trend
                },
                "suggestion": self._derive_suggestion(current_scan, trend)
            }
            
            # 3. Zapis wniosku do Pamięci RAE (Warstwa Reflective)
            await self._store_insight(project_id, insight)
            return insight

        except Exception as e:
            logger.error(f"Kaizen analysis failed: {e}")
            return {"status": "error", "message": str(e)}

    def _derive_suggestion(self, scan: Dict[str, Any], trend: str) -> str:
        """Logika ekspercka wyciągania wniosków."""
        complexity = scan.get("complexity", 0)
        if complexity > 50:
            return "KRYTYCZNE: Złożoność cyklomatyczna przekracza progi. Zalecana dekompozycja modułów."
        if trend == "down":
            return "OSTRZEŻENIE: Spadek jakości w ostatnich commitach. Wymagany audyt Quality Tribunal."
        return "STABILNIE: Kontynuuj obecne wzorce kodowania."

    async def _store_insight(self, project_id: str, insight: Dict[str, Any]):
        """Zapisuje wniosek Kaizen do Pamięci RAE."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.api_url}/v2/memories/", json={
                    "content": f"Kaizen Insight for {project_id}: {insight['suggestion']}",
                    "layer": "reflective",
                    "project": project_id,
                    "metadata": {"insight": insight, "type": "kaizen_report"}
                })
        except Exception as e:
            logger.error(f"Failed to store insight: {e}")
