from fastapi import FastAPI
from typing import List
from rae_lab.hypothesis_engine import HypothesisEngine
from rae_lab.experiment_orchestrator import ExperimentOrchestrator
from rae_lab.strategy_compiler import StrategyCompiler
from rae_lab.safe_rollout_manager import SafeRolloutManager
from rae_core.models.failure import FailureLearningRecord

app = FastAPI(title="RAE-Lab Evolution Engine v3.1")
hyp_engine = HypothesisEngine()
orch = ExperimentOrchestrator()
compiler = StrategyCompiler()
rollout = SafeRolloutManager()

@app.get("/health")
async def health():
    return {"status": "fully_operational", "department": "lab"}

@app.post("/lab/experiment/run")
async def run_experiment(proposal_id: str):
    return orch.run_offline_replay(proposal_id, [])

@app.post("/lab/analyze/failures")
async def analyze_failures(failures: List[FailureLearningRecord]):
    return hyp_engine.generate_from_failures(failures)
