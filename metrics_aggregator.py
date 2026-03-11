# metrics_aggregator.py
import os
import json
import glob
from datetime import datetime

class MetricsAggregator:
    """Zbiera i analizuje wyniki z mikro-evaluatorów RAE."""
    
    def __init__(self, experiments_path="/home/print/cloud/RAE-Lab/experiments"):
        self.path = experiments_path

    def run_daily_report(self):
        print(f"📊 Generowanie raportu RAE-Lab z: {self.path}")
        files = glob.glob(f"{self.path}/*.json")
        
        stats = {
            "total_tasks": 0,
            "avg_score": 0.0,
            "modules": {}
        }
        
        total_score = 0.0
        for f in files:
            with open(f, 'r') as j:
                data = json.load(j)
                stats["total_tasks"] += 1
                total_score += data.get("score", 0.0)
                
                mod = data.get("module", "unknown")
                stats["modules"].setdefault(mod, {"count": 0, "score": 0.0})
                stats["modules"][mod]["count"] += 1
                stats["modules"][mod]["score"] += data.get("score", 0.0)

        if stats["total_tasks"] > 0:
            stats["avg_score"] = total_score / stats["total_tasks"]
            
        print(f"✅ Analiza zakończona. Średni wynik RAE-Suite: {stats['avg_score']:.2f}")
        return stats

if __name__ == "__main__":
    aggregator = MetricsAggregator()
    aggregator.run_daily_report()
