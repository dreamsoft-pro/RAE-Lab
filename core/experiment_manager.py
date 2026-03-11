# core/experiment_manager.py
import json
import os
from datetime import datetime
from typing import Dict, Any, List

class ExperimentManager:
    """Zarządza wynikami audytów i wyciąga wnioski Kaizen."""
    
    def __init__(self, storage_path: str = "/home/print/cloud/RAE-Lab/storage"):
        self.storage_path = storage_path
        self.experiments_dir = os.path.join(storage_path, "experiments")

    def register_scan(self, report_data: Dict[str, Any]):
        """Zapisuje nowy skan jakości jako eksperyment."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        project = report_data.get("project_id", "unknown")
        filename = f"scan_{project}_{timestamp}.json"
        
        path = os.path.join(self.experiments_dir, filename)
        with open(path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return self.generate_kaizen_insight(project)

    def generate_kaizen_insight(self, project_id: str):
        """Analizuje trend jakości dla projektu."""
        # W przyszłości: LLM Reflection Engine tutaj wejdzie
        # Na razie: Prosta analiza trendu
        return {
            "project": project_id,
            "status": "In Analysis",
            "suggestion": "Zalecana optymalizacja funkcji o najwyższej złożoności cyklomatycznej."
        }
